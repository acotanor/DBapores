from flask import Blueprint, jsonify, request, current_app
from app.clients.steam_api_client import SteamApiClient
from app.clients.steamspy_client import SteamSpyClient
from app.repositories.tag_repository import TagRepository
from app.services.steam_library_service import SteamLibraryService
from app.services.tag_profile_service import TagProfileService
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_facade import RecommendationFacade
from app.strategies.relevant_games_strategy import TopPlaytimeRelevantGamesStrategy
from app.strategies.recommendation_sort_strategy import DefaultRecommendationSortStrategy
import requests
import os
import unicodedata
import re

api_bp = Blueprint("api", __name__)
steamSpyCache = {}
STEAMSPY_URL = 'https://steamspy.com/api.php'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TAGS_DIR = os.path.join(BASE_DIR, 'data/tags')
tagFileCache = {}

def build_facade() -> RecommendationFacade:
    config = current_app.config

    steam_client = SteamApiClient(
        api_key=config["STEAM_API_KEY"],
        base_url=config["STEAM_API_BASE_URL"],
        timeout=config["REQUEST_TIMEOUT"],
    )

    steamspy_client = SteamSpyClient(
        base_url=config["STEAMSPY_URL"],
        timeout=config["REQUEST_TIMEOUT"],
    )

    tag_repository = TagRepository(tags_dir=config["TAGS_DIR"])

    relevant_games_strategy = TopPlaytimeRelevantGamesStrategy()
    sort_strategy = DefaultRecommendationSortStrategy()

    steam_library_service = SteamLibraryService(steam_client)
    tag_profile_service = TagProfileService(steamspy_client, relevant_games_strategy)
    recommendation_service = RecommendationService(tag_repository, sort_strategy)

    return RecommendationFacade(
        steam_library_service=steam_library_service,
        tag_profile_service=tag_profile_service,
        recommendation_service=recommendation_service,
    )


@api_bp.get("/recommend")
def recommend():
    steam_id = str(request.args.get("steamId", "")).strip()

    if not steam_id.isdigit() or len(steam_id) != 17:
        return jsonify({"error": "El Steam ID debe ser un SteamID64 de 17 dígitos."}), 400

    if current_app.config["STEAM_API_KEY"] == "TU_API_KEY_AQUI":
        return jsonify({
            "error": "Falta configurar la Steam API Key en la variable de entorno STEAM_API_KEY."
        }), 500

    facade = build_facade()

    try:
        payload = facade.generate_recommendations(steam_id=steam_id, limit=5, top_tags_count=5)
        return jsonify(payload), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception:
        return jsonify({"error": "Ha ocurrido un error interno al generar las recomendaciones."}), 500

@api_bp.get('/recommend_by_game')
def api_recommend_by_game():
    app_id_or_name = request.args.get('appId', '').strip()
    if not app_id_or_name:
        return jsonify({'error': 'El App ID o Nombre no puede estar vacío.'}), 400
    
    app_id = app_id_or_name
    if not app_id.isdigit():
        resolved_id = get_appid_by_name(app_id_or_name)
        if not resolved_id:
            return jsonify({'error': f'No se encontró ningún juego con el nombre "{app_id_or_name}". Asegúrate de escribirlo exactamente o usa el App ID numérico.'}), 404
        app_id = resolved_id
    
    try:
        tags = get_steamspy_tags(app_id, 5)
        
        if not tags:
            return jsonify({'error': 'No se pudieron obtener tags suficientes desde SteamSpy para generar recomendaciones.'}), 404
        
        # Pass the input game as "owned" so it doesn't recommend the exact same game it was queried for
        owned_games = [{'appid': app_id}]
        recommendations, missing_tag_files = recommend_games_from_local_tags(owned_games, top_tags=tags, tags_dir=TAGS_DIR, limit=5)
        
        return jsonify({
            'appId': app_id,
            'topTags': tags,
            'missingTagFiles': missing_tag_files,
            'recommendations': recommendations
        })

    except requests.RequestException as e:
        print(f"Error en /api/recommend_by_game (API request): {e}")
        return jsonify({'error': f'Error de red: {e}'}), 500
    except Exception as e:
        print(f"Error en /api/recommend_by_game: {e}")
        return jsonify({'error': 'Ha ocurrido un error interno al generar las recomendaciones.'}), 500


@api_bp.get('/search_games')
def api_search_games():
    q = request.args.get('q', '').strip().lower()
    if len(q) < 2:
        return jsonify([])
    
    load_app_list()
    results = []
    for game in app_list_cache:
        if q in game['name'].lower():
            results.append(game)
            if len(results) >= 15:
                break
    return jsonify(results)


def get_steamspy_tags(appid, num_tags=5):
    cache_key = f"{appid}:{num_tags}"
    if cache_key in steamSpyCache:
        return steamSpyCache[cache_key]
    
    try:
        resp = requests.get(STEAMSPY_URL, params={'request': 'appdetails', 'appid': appid}, timeout=15)
        if not resp.ok:
            steamSpyCache[cache_key] = []
            return []
        
        data = resp.json()
        tags_object = data.get('tags')
        
        if not tags_object or not isinstance(tags_object, dict):
            steamSpyCache[cache_key] = []
            return []
        
        tags_sorted = sorted(tags_object.items(), key=lambda x: int(x[1]), reverse=True)
        tags = [str(k).lower() for k, v in tags_sorted[:num_tags]]
        
        steamSpyCache[cache_key] = tags
        return tags
    except Exception:
        steamSpyCache[cache_key] = []
        return []


def recommend_games_from_local_tags(owned_games, top_tags, tags_dir, limit=5):
    owned_ids = {str(g['appid']) for g in owned_games}
    candidates = {}
    missing_tag_files = []
    
    for tag in top_tags:
        tag_games = load_tag_games(tag, tags_dir)
        if not tag_games:
            missing_tag_files.append(tag)
            continue
        
        for game in tag_games:
            appid = str(game.get('appid', '')).strip()
            if not appid or appid in owned_ids:
                continue
            
            name = game.get('name', 'Sin nombre')
            positive = int(game.get('positive', 0))
            relevancia = float(game.get('relevancia', 0))
            
            if appid not in candidates:
                candidates[appid] = {
                    'appid': appid,
                    'name': name,
                    'positive': positive,
                    'coincidencias': 0,
                    'tagsCoincidentes': set(),
                    'relevancia_total': 0,
                    'relevancia_max': 0
                }
            
            c = candidates[appid]
            c['tagsCoincidentes'].add(tag)
            c['relevancia_total'] += relevancia
            c['relevancia_max'] = max(c['relevancia_max'], relevancia)
            c['positive'] = max(c['positive'], positive)

    recommendations_list = []
    for c in candidates.values():
        tags_coincidentes = sorted(list(c['tagsCoincidentes']))
        rec = {
            **c,
            'coincidencias': len(tags_coincidentes),
            'tagsCoincidentes': tags_coincidentes,
            'steamUrl': f"https://store.steampowered.com/app/{c['appid']}/"
        }
        recommendations_list.append(rec)
    
    recommendations_list.sort(key=lambda x: (
        -x['coincidencias'],
        -x['relevancia_total'],
        -x['relevancia_max'],
        -x['positive'],
        x['name'].lower()
    ))
    
    return recommendations_list[:limit], missing_tag_files

def load_tag_games(tag, tags_dir):
    file_name = f"{normalize_tag_to_file_name(tag)}.json"
    file_path = os.path.join(tags_dir, file_name)
    
    if file_path in tagFileCache:
        return tagFileCache[file_path]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            parsed = json.load(f)
            games = parsed if isinstance(parsed, list) else []
            tagFileCache[file_path] = games
            return games
    except Exception:
        tagFileCache[file_path] = []
        return []

def normalize_tag_to_file_name(tag):
    tag = unicodedata.normalize('NFD', tag.strip().lower())
    tag = ''.join(c for c in tag if unicodedata.category(c) != 'Mn')
    tag = tag.replace('&', 'and')
    tag = re.sub(r'[ \-]+', '_', tag)
    tag = re.sub(r'[^a-z0-9_]', '', tag)
    tag = re.sub(r'_+', '_', tag)
    return tag.strip('_')