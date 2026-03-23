from collections import Counter


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

        for game in relevant_games:
            tags = self.steamspy_client.get_top_tags(
                appid=game["appid"],
                num_tags=steamspy_tags_per_game
            )
            tag_counter.update(tags)

        top_tags = [
            tag for tag, _count in sorted(
                tag_counter.items(),
                key=lambda item: (-item[1], item[0])
            )[:top_tags_count]
        ]

        return top_tags, relevant_games