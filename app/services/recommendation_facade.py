class RecommendationFacade:
    def __init__(self, steam_library_service, tag_profile_service, recommendation_service, game_catalog_service):
        self.steam_library_service = steam_library_service
        self.tag_profile_service = tag_profile_service
        self.recommendation_service = recommendation_service
        self.game_catalog_service = game_catalog_service

    def _process_featured_and_fallback(self, all_recs, owned_ids_set=None):
        """Extracts featured games and fills remaining slots with random sponsored ones."""
        if owned_ids_set is None:
            owned_ids_set = set()

        featured = [r for r in all_recs if r.get("coincidencias", 0) >= 100]
        normal = [r for r in all_recs if r.get("coincidencias", 0) < 100]
        
        featured_ids = {str(r["appid"]) for r in featured}
        all_sponsored_ids = list(self.recommendation_service.sponsored_ids)
        
        import random
        random.shuffle(all_sponsored_ids)
        
        for sid in all_sponsored_ids:
            if len(featured) >= 3:
                break
            if sid not in featured_ids and sid not in owned_ids_set:
                game_info = self.game_catalog_service.get_game_by_id(sid)
                if game_info:
                    featured.append({
                        "appid": sid,
                        "name": game_info["name"],
                        "tagsCoincidentes": [],
                        "steamUrl": f"https://store.steampowered.com/app/{sid}/",
                        "is_sponsored": True,
                        "coincidencias": 100
                    })
                    featured_ids.add(sid)
        
        return featured[:3], normal[:5]

    def recommend_by_game(self, app_id_or_name: str, limit: int = 5) -> dict:
        """Generates recommendations based on a single game."""
        app_id = app_id_or_name
        if not app_id.isdigit():
            resolved_id = self.game_catalog_service.get_appid_by_name(app_id_or_name)
            if not resolved_id:
                raise ValueError(f"No se encontró ningún juego con el nombre '{app_id_or_name}'.")
            app_id = resolved_id
        
        # Use SteamSpy to get tags for this specific game
        steamspy_client = self.tag_profile_service.steamspy_client
        tags = steamspy_client.get_top_tags(app_id, 5)
        
        if not tags:
            raise ValueError(f"No se pudieron obtener etiquetas para el juego {app_id}.")

        # For single game recommendation, "owned_games" is just this game to avoid recommending it back
        owned_games = [{"appid": app_id}]
        
        recommendations, missing_tag_files = self.recommendation_service.recommend_from_tags(
            owned_games=owned_games,
            top_tags=tags,
            limit=limit
        )
        
        owned_ids = {str(app_id)}
        featured, normal = self._process_featured_and_fallback(recommendations, owned_ids)
        
        return {
            "appId": app_id,
            "topTags": tags,
            "missingTagFiles": missing_tag_files,
            "recommendations": normal,
            "featured": featured
        }

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

        owned_ids = {str(g.get('appid')) for g in owned_games}
        if limit == 0:
            featured = []
            normal = recommendations
        else:
            featured, normal = self._process_featured_and_fallback(recommendations, owned_ids)

        return {
            "steamId": steam_id,
            "topTags": top_tags,
            "missingTagFiles": missing_tag_files,
            "recommendations": normal,
            "featured": featured,
            "ownedGames": owned_games,
            "stats": {
                "totalOwnedGames": len(owned_games),
                "relevantGamesAnalyzed": len(relevant_games)
            }
        }