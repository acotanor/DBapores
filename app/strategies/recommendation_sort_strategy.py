from abc import ABC, abstractmethod


class RecommendationSortStrategy(ABC):
    @abstractmethod
    def sort(self, candidates: list[dict]) -> list[dict]:
        pass


class DefaultRecommendationSortStrategy(RecommendationSortStrategy):
    def sort(self, candidates: list[dict]) -> list[dict]:
        return sorted(
            candidates,
            key=lambda game: (
                -game["coincidencias"],
                -game["relevancia_total"],
                -game["relevancia_max"],
                -game["positive"],
                game["name"].lower(),
            )
        )