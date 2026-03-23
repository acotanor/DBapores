from abc import ABC, abstractmethod
import math


class RelevantGamesStrategy(ABC):
    @abstractmethod
    def select_games(self, games: list[dict]) -> list[dict]:
        pass


class TopPlaytimeRelevantGamesStrategy(RelevantGamesStrategy):
    def select_games(self, games: list[dict]) -> list[dict]:
        if not games:
            return []

        sorted_games = sorted(
            games,
            key=lambda game: game.get("playtime_forever", 0),
            reverse=True
        )

        if len(sorted_games) < 30:
            return sorted_games

        amount = math.ceil(len(sorted_games) * 0.30)
        return sorted_games[:amount]