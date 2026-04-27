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
import json
import csv

api_bp = Blueprint("api", __name__)

# --- Configuration and Caches ---
steamSpyCache = {}
STEAMSPY_URL = 'https://steamspy.com/api.php'
# __file__ is repo/app/controllers/api_controller.py. 
# Go up 3 levels to reach the root directory.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAGS_DIR = os.path.join(BASE_DIR, 'data', 'tags')
APP_LIST_PATH = os.path.join(BASE_DIR, 'data', 'app_list.csv')

tagFileCache = {}
app_list_cache = []
app_name_to_id_cache = {}
app_list_loaded = False
_shared_clients = {}

def build_facade() -> RecommendationFacade:
    """Configures the recommendation engine using dependency injection."""
    config = current_app.config

    steam_client = SteamApiClient(
        api_key=config["STEAM_API_KEY"],
        base_url=config["STEAM_API_BASE_URL"],
        timeout=config["REQUEST_TIMEOUT"],
    )
    # Reuse a shared SteamSpyClient across requests to keep its internal cache
    # (avoids re-requesting the same app details on every request).
    if 'steamspy' not in _shared_clients:
        _shared_clients['steamspy'] = SteamSpyClient(
            base_url=config["STEAMSPY_URL"],
            timeout=config["REQUEST_TIMEOUT"],
        )
    steamspy_client = _shared_clients['steamspy']
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

# --- Helper Functions ---

def normalize_search_name(name):
    """
    Strips symbols like ® and ™ to ensure robust matches.
    """
    if not name:
        return ""
    # NFKD normalization separates base characters from their marks.
    name = unicodedata.normalize('NFKD', name.strip().lower())
    # Remove registered trademark, trademark, and copyright symbols.
    name = re.sub(r'[®™©]', '', name)
    # Remove extra whitespace.
    return re.sub(r'\s+', ' ', name).strip()

def load_app_list():
    """Loads the CSV into memory caches for searching and name resolution."""
    global app_list_loaded
    if not app_list_loaded:
        app_list_loaded = True
        try:
            with open(APP_LIST_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip CSV header
                for row in reader:
                    if len(row) >= 2:
                        appid, game_name = row[0], row[1]
                        # Store using the clean version for the dictionary key.
                        clean_name = normalize_search_name(game_name)
                        app_name_to_id_cache[clean_name] = appid
                        # Keep original name for display purposes in the UI.
                        app_list_cache.append({'id': appid, 'name': game_name.strip()})
        except Exception as e:
            print(f"Error loading app_list.csv: {e}")

def get_appid_by_name(name):
    """Resolves a game name to its App ID using normalized matching."""
    load_app_list()
    return app_name_to_id_cache.get(normalize_search_name(name))

# --- API Routes ---

@api_bp.get("/recommend")
def recommend():
    """Generates recommendations based on a user's Steam ID."""
    steam_id = str(request.args.get("steamId", "")).strip()

    if not steam_id.isdigit() or len(steam_id) != 17:
        return jsonify({"error": "El Steam ID debe ser un SteamID de 17 dígitos."}), 400

    if current_app.config["STEAM_API_KEY"] == "TU_API_KEY_AQUI":
        return jsonify({"error": "Falta configurar la Steam API Key."}), 500

    facade = build_facade()
    try:
        payload = facade.generate_recommendations(steam_id=steam_id, limit=5, top_tags_count=5)
        return jsonify(payload), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception:
        return jsonify({"error": "Error interno al generar las recomendaciones."}), 500


@api_bp.get('/wrapped/<steam_id>')
def wrapped(steam_id: str):
    """Prototype 'Steam Wrapped' endpoint. Returns JSON and renders a simple HTML report if
    the request accepts HTML.
    """
    steam_id = str(steam_id).strip()

    if not steam_id.isdigit() or len(steam_id) != 17:
        return jsonify({"error": "El Steam ID debe ser un SteamID de 17 dígitos."}), 400

    facade = build_facade()
    try:
        # Generate recommendations and top tags using existing facade
        payload = facade.generate_recommendations(steam_id=steam_id, limit=10, top_tags_count=10)

        # Derive top games and total playtime from owned games
        owned_games = payload.get('stats', {}).get('relevantGamesAnalyzed')
        # Note: `generate_recommendations` does not return owned games; fetch directly
        steam_lib = facade.steam_library_service
        owned = steam_lib.get_owned_games(steam_id)

        # Compute top games by playtime (field names may vary; use 'playtime_forever' or 'playtime')
        def playtime_of(g):
            for k in ('playtime_forever', 'playtime', 'playtime_hours'):
                if k in g and g[k] is not None:
                    try:
                        return float(g[k])
                    except Exception:
                        pass
            return 0.0

        top_games = sorted(owned, key=playtime_of, reverse=True)[:10]
        total_playtime = sum(playtime_of(g) for g in owned)

        # Convert playtime (likely minutes) to hours for display
        def to_hours(minutes):
            try:
                return round(float(minutes) / 60.0, 1)
            except Exception:
                return 0.0

        top_games_items = []
        for g in top_games:
            appid = str(g.get('appid', ''))
            top_games_items.append({
                'appid': appid,
                'name': g.get('name', ''),
                'playtime': playtime_of(g),
                'playtime_hours': to_hours(playtime_of(g)),
                'image': f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
            })

        # Attach images for recommendations when possible
        recs = payload.get('recommendations', [])
        for r in recs:
            try:
                r_appid = r.get('appid') or r.get('id') or ''
                r['image'] = f"https://cdn.akamai.steamstatic.com/steam/apps/{r_appid}/header.jpg"
            except Exception:
                r['image'] = None

        report = {
            'steamId': steam_id,
            'topTags': payload.get('topTags', []),
            'topGames': top_games_items,
            'totalPlaytime': total_playtime,
            'totalPlaytimeHours': to_hours(total_playtime),
            'recommendations': payload.get('recommendations', []),
            'missingTagFiles': payload.get('missingTagFiles', []),
            'stats': payload.get('stats', {})
        }

        # If the client accepts HTML, render a simple template; otherwise return JSON
        accept = request.headers.get('Accept', '')
        if 'text/html' in accept:
            try:
                return current_app.jinja_env.get_or_select_template(['wrapped.html']).render(report=report), 200
            except Exception:
                # Fallback to JSON if template not found or render fails
                return jsonify(report), 200

        return jsonify(report), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as e:
        print(f"Error generating wrapped for {steam_id}: {e}")
        return jsonify({"error": "Error interno al generar el Wrapped."}), 500

@api_bp.get('/recommend_by_game')
def api_recommend_by_game():
    """Generates recommendations based on a single game ID or name."""
    app_id_or_name = request.args.get('appId', '').strip()
    if not app_id_or_name:
        return jsonify({'error': 'El App ID o Nombre no puede estar vacío.'}), 400
    
    app_id = app_id_or_name
    if not app_id.isdigit():
        resolved_id = get_appid_by_name(app_id_or_name)
        if not resolved_id:
            return jsonify({'error': f'No se encontró ningún juego con el nombre "{app_id_or_name}".'}), 404
        app_id = resolved_id
    
    try:
        tags = get_steamspy_tags(app_id, 5)
        if not tags:
            # Check if it was a specifically caught error or just empty
            return jsonify({
                'error': f'No se pudieron obtener tags para el juego (AppID: {app_id}). '
                         'Verifica la conexión con SteamSpy o si el ID es correcto.'
            }), 502
        
        owned_games = [{'appid': app_id}]
        recommendations, missing_tag_files = recommend_games_from_local_tags(
            owned_games, top_tags=tags, tags_dir=TAGS_DIR, limit=5
        )
        
        return jsonify({
            'appId': app_id,
            'topTags': tags,
            'missingTagFiles': missing_tag_files,
            'recommendations': recommendations
        })
    except Exception as e:
        print(f"Error en /api/recommend_by_game: {e}")
        return jsonify({'error': 'Error interno al generar las recomendaciones.'}), 500

@api_bp.get('/search_games')
def api_search_games():
    """Filters the app list for search suggestions."""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    
    load_app_list()
    clean_q = normalize_search_name(q)
    results = []
    
    for game in app_list_cache:
        # Check against the normalized version so symbols don't prevent matches.
        if clean_q in normalize_search_name(game['name']):
            results.append(game)
            if len(results) >= 15:
                break
    return jsonify(results)

# --- SteamSpy & Tag Processing ---

def get_steamspy_tags(appid, num_tags=5):
    """Fetches top tags for an AppID from SteamSpy."""
    cache_key = f"{appid}:{num_tags}"
    if cache_key in steamSpyCache:
        return steamSpyCache[cache_key]
    
    try:
        resp = requests.get(STEAMSPY_URL, params={'request': 'appdetails', 'appid': appid}, timeout=15)
        if not resp.ok:
            print(f"DEBUG: SteamSpy API error for {appid}: HTTP {resp.status_code}")
            return []
        
        data = resp.json()
        if not data or not isinstance(data, dict):
            print(f"DEBUG: SteamSpy returned invalid JSON for {appid}")
            return []
            
        tags_object = data.get('tags')
        
        if not tags_object or not isinstance(tags_object, dict):
            print(f"DEBUG: No tags found in SteamSpy response for {appid}. Checking genre.")
            genre_str = data.get('genre', '')
            if genre_str and isinstance(genre_str, str):
                genres = [g.strip().lower() for g in genre_str.split(',') if g.strip()]
                print(f"DEBUG: Using genre fallback for {appid}: {genres}")
                tags = genres[:num_tags]
                steamSpyCache[cache_key] = tags
                return tags
                
            if 'name' in data:
                print(f"DEBUG: Game found: {data['name']}, but no tags or genre.")
            return []
        
        # Sort tags by frequency, handling potential non-integer values safely
        try:
            tags_sorted = sorted(
                tags_object.items(), 
                key=lambda x: int(str(x[1]).replace(',', '') if x[1] else 0), 
                reverse=True
            )
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Error sorting tags for {appid}: {e}")
            tags_sorted = list(tags_object.items())

        tags = [str(k).lower() for k, v in tags_sorted[:num_tags]]
        
        steamSpyCache[cache_key] = tags
        return tags
    except Exception as e:
        print(f"DEBUG: Exception in get_steamspy_tags for {appid}: {e}")
        return []

def recommend_games_from_local_tags(owned_games, top_tags, tags_dir, limit=5):
    """Calculates game scores based on overlapping local tag JSON files."""
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
            
            if appid not in candidates:
                candidates[appid] = {
                    'appid': appid,
                    'name': game.get('name', 'Sin nombre'),
                    'positive': int(game.get('positive', 0)),
                    'tagsCoincidentes': set(),
                    'relevancia_total': 0,
                    'relevancia_max': 0
                }
            
            c = candidates[appid]
            relevancia = float(game.get('relevancia', 0))
            c['tagsCoincidentes'].add(tag)
            c['relevancia_total'] += relevancia
            c['relevancia_max'] = max(c['relevancia_max'], relevancia)

    recommendations_list = []
    for c in candidates.values():
        tags_coincidentes = sorted(list(c['tagsCoincidentes']))
        recommendations_list.append({
            **c,
            'coincidencias': len(tags_coincidentes),
            'tagsCoincidentes': tags_coincidentes,
            'steamUrl': f"https://store.steampowered.com/app/{c['appid']}/"
        })
    
    # Sort by matches first, then relevance.
    recommendations_list.sort(key=lambda x: (
        -x['coincidencias'],
        -x['relevancia_total'],
        -x['relevancia_max'],
        -x['positive'],
        x['name'].lower()
    ))
    
    return recommendations_list[:limit], missing_tag_files

def load_tag_games(tag, tags_dir):
    """Loads a specific tag's JSON file and caches the content."""
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
        return []

def normalize_tag_to_file_name(tag):
    """Converts a tag name into a valid filesystem filename."""
    tag = unicodedata.normalize('NFD', tag.strip().lower())
    tag = ''.join(c for c in tag if unicodedata.category(c) != 'Mn')
    tag = tag.replace('&', 'and')
    tag = re.sub(r'[ \-]+', '_', tag)
    tag = re.sub(r'[^a-z0-9_]', '', tag)
    tag = re.sub(r'_+', '_', tag)
    return tag.strip('_')