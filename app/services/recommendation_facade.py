class RecommendationFacade:
    def __init__(self, steam_library_service, tag_profile_service, recommendation_service):
        self.steam_library_service = steam_library_service
        self.tag_profile_service = tag_profile_service
        self.recommendation_service = recommendation_service

    def generate_recommendations(self, steam_id: str, limit: int = 5, top_tags_count: int = 5) -> dict:
        owned_games = self.steam_library_service.get_owned_games(steam_id)

        if not owned_games:
            raise ValueError(
                "No se ha podido leer la biblioteca. Revisa que el Steam ID sea correcto y que el perfil/juegos sean públicos."
            )

        top_tags, relevant_games = self.tag_profile_service.build_top_tags_profile(
            owned_games=owned_games,
            top_tags_count=top_tags_count,
            steamspy_tags_per_game=5
        )

        if not top_tags:
            raise ValueError(
                "No se pudieron obtener tags suficientes desde SteamSpy para generar recomendaciones."
            )

        recommendations, missing_tag_files = self.recommendation_service.recommend_from_tags(
            owned_games=owned_games,
            top_tags=top_tags,
            limit=limit
        )

        return {
            "steamId": steam_id,
            "topTags": top_tags,
            "missingTagFiles": missing_tag_files,
            "recommendations": recommendations,
            "stats": {
                "totalOwnedGames": len(owned_games),
                "relevantGamesAnalyzed": len(relevant_games)
            }
        }