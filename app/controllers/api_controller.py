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

api_bp = Blueprint("api", __name__)


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