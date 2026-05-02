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
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils.disk_cache import DiskCache
from app.services.game_catalog_service import GameCatalogService

api_bp = Blueprint("api", __name__)

# --- Configuration ---
_shared_clients = {}

def build_facade() -> RecommendationFacade:
    """Configures the recommendation engine using dependency injection."""
    config = current_app.config

    steam_client = SteamApiClient(
        api_key=config["STEAM_API_KEY"],
        base_url=config["STEAM_API_BASE_URL"],
        timeout=config["REQUEST_TIMEOUT"],
    )
    
    # Reuse a shared DiskCache across requests
    if 'cache' not in _shared_clients:
        _shared_clients['cache'] = DiskCache(config["CACHE_DIR"])
    disk_cache = _shared_clients['cache']

    if 'steamspy' not in _shared_clients:
        _shared_clients['steamspy'] = SteamSpyClient(
            base_url=config["STEAMSPY_URL"],
            timeout=config["REQUEST_TIMEOUT"],
            disk_cache=disk_cache
        )
    steamspy_client = _shared_clients['steamspy']
    tag_repository = TagRepository(tags_dir=config["TAGS_DIR"])

    relevant_games_strategy = TopPlaytimeRelevantGamesStrategy()
    sort_strategy = DefaultRecommendationSortStrategy()

    steam_library_service = SteamLibraryService(steam_client, disk_cache)
    tag_profile_service = TagProfileService(steamspy_client, relevant_games_strategy)
    recommendation_service = RecommendationService(
        tag_repository, 
        sort_strategy, 
        sponsored_path=config.get("SPONSORED_APPS_PATH")
    )
    game_catalog_service = GameCatalogService(config["APP_LIST_PATH"])

    return RecommendationFacade(
        steam_library_service=steam_library_service,
        tag_profile_service=tag_profile_service,
        recommendation_service=recommendation_service,
        game_catalog_service=game_catalog_service
    )

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
        # Generate recommendations (facade now handles fallback internally)
        payload = facade.generate_recommendations(steam_id=steam_id, limit=15, top_tags_count=5)
        return jsonify(payload), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception:
        return jsonify({"error": "Error interno al generar las recomendaciones."}), 500


@api_bp.get('/wrapped/<steam_id>')
def wrapped(steam_id: str):
    """Prototype 'Steam Wrapped' endpoint."""
    steam_id = str(steam_id).strip()

    if not steam_id.isdigit() or len(steam_id) != 17:
        return jsonify({"error": "El Steam ID debe ser un SteamID de 17 dígitos."}), 400

    facade = build_facade()
    steam_api_key = current_app.config.get("STEAM_API_KEY", "")
    try:
        payload = facade.generate_recommendations(steam_id=steam_id, limit=0, top_tags_count=10)
        owned = payload.get('ownedGames', [])

        def playtime_of(g):
            for k in ('playtime_forever', 'playtime', 'playtime_hours'):
                if k in g and g[k] is not None:
                    try:
                        return float(g[k])
                    except Exception:
                        pass
            return 0.0

        top_games = sorted(owned, key=playtime_of, reverse=True)[:15]
        total_playtime = sum(playtime_of(g) for g in owned)

        def to_hours(minutes):
            try:
                return round(float(minutes) / 60.0, 1)
            except Exception:
                return 0.0

        top_games_items = []
        all_achievements = []
        
        for g in top_games:
            appid = str(g.get('appid', ''))
            game_name = g.get('name', 'Sin nombre')
            top_games_items.append({
                'appid': appid,
                'name': game_name,
                'playtime': playtime_of(g),
                'playtime_hours': to_hours(playtime_of(g)),
                'image': f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
            })
            
        if steam_api_key:
            steam_lib = facade.steam_library_service
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(steam_lib.get_game_achievements, steam_id, g) for g in top_games]
                for fut in as_completed(futures):
                    res = fut.result()
                    if res:
                        all_achievements.append(res)

        report = {
            'steamId': steam_id,
            'topTags': payload.get('topTags', []),
            'topGames': top_games_items,
            'achievements': all_achievements,
            'totalPlaytime': total_playtime,
            'totalPlaytimeHours': to_hours(total_playtime),
            'stats': payload.get('stats', {})
        }

        accept = request.headers.get('Accept', '')
        if 'text/html' in accept:
            try:
                return current_app.jinja_env.get_or_select_template(['wrapped.html']).render(report=report), 200
            except Exception:
                return jsonify(report), 200

        return jsonify(report), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as e:
        print(f"Error generating wrapped for {steam_id}: {e}")
        return jsonify({"error": "Error interno al generar el Wrapped."}), 500

@api_bp.get('/wrapped_filtered')
def wrapped_filtered():
    """Returns top games and achievements filtered by a specific tag."""
    steam_id = request.args.get('steamId', '').strip()
    tag = request.args.get('tag', '').strip()
    
    if not steam_id or not tag:
        return jsonify({"error": "Faltan parámetros steamId o tag."}), 400

    facade = build_facade()
    steam_api_key = current_app.config.get("STEAM_API_KEY", "")

    try:
        steam_lib = facade.steam_library_service
        owned = steam_lib.get_owned_games(steam_id)
        owned_dict = {str(g.get('appid')): g for g in owned}
        
        # Use TagRepository from recommendation service
        tag_games = facade.recommendation_service.tag_repository.load_games_by_tag(tag)
        if not tag_games:
            return jsonify({"topGames": [], "achievements": []}), 200
            
        matched_games = []
        for tg in tag_games:
            appid = str(tg.get('appid', ''))
            if appid in owned_dict:
                matched_games.append(owned_dict[appid])
                
        def playtime_of(g):
            for k in ('playtime_forever', 'playtime', 'playtime_hours'):
                if k in g and g[k] is not None:
                    try:
                        return float(g[k])
                    except Exception:
                        pass
            return 0.0

        def to_hours(minutes):
            try:
                return round(float(minutes) / 60.0, 1)
            except Exception:
                return 0.0
                
        top_games = sorted(matched_games, key=playtime_of, reverse=True)[:5]
        
        top_games_items = []
        all_achievements = []
        
        for g in top_games:
            appid = str(g.get('appid', ''))
            game_name = g.get('name', 'Sin nombre')
            top_games_items.append({
                'appid': appid,
                'name': game_name,
                'playtime': playtime_of(g),
                'playtime_hours': to_hours(playtime_of(g)),
                'image': f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
            })
            
        if steam_api_key:
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(steam_lib.get_game_achievements, steam_id, g) for g in top_games]
                for fut in as_completed(futures):
                    res = fut.result()
                    if res:
                        all_achievements.append(res)

        return jsonify({
            "topGames": top_games_items,
            "achievements": all_achievements
        }), 200
    except Exception as e:
        print(f"Error filtering wrapped top games: {e}")
        return jsonify({"error": "Error interno"}), 500

@api_bp.get('/recommend_by_game')
def api_recommend_by_game():
    """Generates recommendations based on a single game ID or name."""
    app_id_or_name = request.args.get('appId', '').strip()
    if not app_id_or_name:
        return jsonify({'error': 'El App ID o Nombre no puede estar vacío.'}), 400
    
    facade = build_facade()
    try:
        # Generate recommendations (facade now handles fallback internally)
        data = facade.recommend_by_game(app_id_or_name, limit=15)
        return jsonify(data), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as e:
        print(f"Error en /api/recommend_by_game: {e}")
        return jsonify({'error': 'Error interno al generar las recomendaciones.'}), 500

@api_bp.get('/search_games')
def api_search_games():
    """Filters the app list for search suggestions."""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    
    facade = build_facade()
    results = facade.game_catalog_service.search_games(q)
    return jsonify(results)