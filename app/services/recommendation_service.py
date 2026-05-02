import json
import os

class RecommendationService:
    def __init__(self, tag_repository, sort_strategy, sponsored_path=None):
        self.tag_repository = tag_repository
        self.sort_strategy = sort_strategy
        self.sponsored_path = sponsored_path
        self.sponsored_ids = self._load_sponsored_ids()

    def _load_sponsored_ids(self):
        if not self.sponsored_path or not os.path.exists(self.sponsored_path):
            return set()
        try:
            with open(self.sponsored_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(str(sid) for sid in data.get('sponsored_appids', []))
        except Exception:
            return set()

    def recommend_from_tags(self, owned_games: list[dict], top_tags: list[str], limit: int = 8):
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
                        "is_sponsored": appid in self.sponsored_ids
                    }

                candidate = candidates[appid]
                candidate["tagsCoincidentes"].add(tag)
                candidate["relevancia_total"] += float(game["relevancia"])
                candidate["relevancia_max"] = max(candidate["relevancia_max"], float(game["relevancia"]))
                candidate["positive"] = max(candidate["positive"], int(game["positive"]))

        normalized_candidates = []
        for candidate in candidates.values():
            tags = sorted(candidate["tagsCoincidentes"])
            
            # Smart Boosting: Only boost if it's sponsored AND relevant (relevance >= 0.6)
            coincidencias = len(tags)
            if candidate["is_sponsored"] and candidate["relevancia_max"] >= 0.6:
                coincidencias += 100

            normalized_candidates.append({
                **candidate,
                "coincidencias": coincidencias,
                "tagsCoincidentes": tags,
                "steamUrl": f"https://store.steampowered.com/app/{candidate['appid']}/"
            })

        recommendations = self.sort_strategy.sort(normalized_candidates)[:limit]
        return recommendations, missing_tag_files
    