class RecommendationService:
    def __init__(self, tag_repository, sort_strategy):
        self.tag_repository = tag_repository
        self.sort_strategy = sort_strategy

    def recommend_from_tags(self, owned_games: list[dict], top_tags: list[str], limit: int = 5):
        owned_ids = {str(game["appid"]) for game in owned_games}
        candidates = {}
        missing_tag_files = []

        for tag in top_tags:
            tag_games = self.tag_repository.load_games_by_tag(tag)

            if not tag_games:
                missing_tag_files.append(tag)
                continue

            for game in tag_games:
                appid = str(game["appid"]).strip()

                if not appid or appid in owned_ids:
                    continue

                if appid not in candidates:
                    candidates[appid] = {
                        "appid": appid,
                        "name": game["name"],
                        "positive": int(game["positive"]),
                        "coincidencias": 0,
                        "tagsCoincidentes": set(),
                        "relevancia_total": 0.0,
                        "relevancia_max": 0.0,
                    }

                candidate = candidates[appid]
                candidate["tagsCoincidentes"].add(tag)
                candidate["relevancia_total"] += float(game["relevancia"])
                candidate["relevancia_max"] = max(candidate["relevancia_max"], float(game["relevancia"]))
                candidate["positive"] = max(candidate["positive"], int(game["positive"]))

        normalized_candidates = []
        for candidate in candidates.values():
            tags = sorted(candidate["tagsCoincidentes"])
            normalized_candidates.append({
                **candidate,
                "coincidencias": len(tags),
                "tagsCoincidentes": tags,
                "steamUrl": f"https://store.steampowered.com/app/{candidate['appid']}/"
            })

        recommendations = self.sort_strategy.sort(normalized_candidates)[:limit]
        return recommendations, missing_tag_files
    