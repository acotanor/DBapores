from __future__ import annotations

import pytest

from app.strategies.relevant_games_strategy import TopPlaytimeRelevantGamesStrategy


def _g(appid: str, playtime: int | None):
    g = {"appid": appid}
    if playtime is not None:
        g["playtime_forever"] = playtime
    return g


def test_select_games_returns_empty_list_when_input_empty():
    strategy = TopPlaytimeRelevantGamesStrategy()
    assert strategy.select_games([]) == []


def test_select_games_sorts_by_playtime_desc_and_returns_all_when_under_30():
    strategy = TopPlaytimeRelevantGamesStrategy()
    games = [_g("a", 5), _g("b", 100), _g("c", 0), _g("d", None)]

    selected = strategy.select_games(games)

    assert [g["appid"] for g in selected] == ["b", "a", "c", "d"]


def test_select_games_returns_top_30_percent_ceiled_when_30_games():
    strategy = TopPlaytimeRelevantGamesStrategy()

    games = [{"appid": str(i), "playtime_forever": i} for i in range(30)]
    selected = strategy.select_games(games)

    # ceil(30 * 0.30) = 9
    assert len(selected) == 9
    assert [g["appid"] for g in selected] == [str(i) for i in range(29, 20, -1)]


def test_select_games_ceils_amount_when_31_games():
    strategy = TopPlaytimeRelevantGamesStrategy()

    games = [{"appid": str(i), "playtime_forever": i} for i in range(31)]
    selected = strategy.select_games(games)

    # ceil(31 * 0.30) = ceil(9.3) = 10
    assert len(selected) == 10
    assert selected[0]["appid"] == "30"
    assert selected[-1]["appid"] == "21"
