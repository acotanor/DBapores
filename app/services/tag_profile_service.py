from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed


class TagProfileService:
    def __init__(self, steamspy_client, relevant_games_strategy):
        self.steamspy_client = steamspy_client
        self.relevant_games_strategy = relevant_games_strategy

    def build_top_tags_profile(
        self,
        owned_games: list[dict],
        top_tags_count: int = 5,
        steamspy_tags_per_game: int = 5
    ) -> tuple[list[str], list[dict]]:
        relevant_games = self.relevant_games_strategy.select_games(owned_games)
        tag_counter = Counter()

        # Parallelize SteamSpy requests to reduce wall-clock time when
        # querying multiple games. The SteamSpy client keeps an internal
        # cache so repeated calls are cheap.
        if relevant_games:
            max_workers = min(15, len(relevant_games))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self.steamspy_client.get_top_tags, game["appid"], steamspy_tags_per_game)
                    for game in relevant_games
                ]
                for fut in as_completed(futures):
                    try:
                        tags = fut.result()
                    except Exception:
                        tags = []
                    tag_counter.update(tags)

        top_tags = [
            tag for tag, _count in sorted(
                tag_counter.items(),
                key=lambda item: (-item[1], item[0])
            )[:top_tags_count]
        ]

        return top_tags, relevant_games