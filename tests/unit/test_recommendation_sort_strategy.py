from __future__ import annotations

from app.strategies.recommendation_sort_strategy import DefaultRecommendationSortStrategy


def _c(
    appid: str,
    name: str,
    coincidencias: int,
    relevancia_total: float,
    relevancia_max: float,
    positive: int,
):
    return {
        "appid": appid,
        "name": name,
        "coincidencias": coincidencias,
        "relevancia_total": relevancia_total,
        "relevancia_max": relevancia_max,
        "positive": positive,
    }


def test_sort_orders_by_coincidencias_desc_first():
    s = DefaultRecommendationSortStrategy()
    candidates = [
        _c("1", "B", 1, 0, 0, 0),
        _c("2", "A", 3, 0, 0, 0),
        _c("3", "C", 2, 0, 0, 0),
    ]

    sorted_out = s.sort(candidates)
    assert [c["appid"] for c in sorted_out] == ["2", "3", "1"]


def test_sort_uses_relevancia_total_then_relevancia_max_then_positive_as_tie_breakers():
    s = DefaultRecommendationSortStrategy()
    candidates = [
        _c("1", "X", 2, 1.0, 0.1, 10),
        _c("2", "X", 2, 2.0, 0.1, 10),  # higher relevancia_total
        _c("3", "X", 2, 2.0, 0.9, 10),  # higher relevancia_max
        _c("4", "X", 2, 2.0, 0.9, 99),  # higher positive
    ]

    sorted_out = s.sort(candidates)
    assert [c["appid"] for c in sorted_out] == ["4", "3", "2", "1"]


def test_sort_uses_name_case_insensitive_for_final_tie_breaker():
    s = DefaultRecommendationSortStrategy()
    candidates = [
        _c("1", "beta", 1, 0, 0, 0),
        _c("2", "Alpha", 1, 0, 0, 0),
        _c("3", "ALPHA", 1, 0, 0, 0),
    ]

    sorted_out = s.sort(candidates)
    # "Alpha" and "ALPHA" compare equal by lower(), so their relative order is stable.
    assert [c["appid"] for c in sorted_out] == ["2", "3", "1"]
