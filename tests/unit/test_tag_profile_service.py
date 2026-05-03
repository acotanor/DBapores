from __future__ import annotations

import threading

import pytest

from app.services.tag_profile_service import TagProfileService


pytestmark = pytest.mark.unit


class FakeRelevantGamesStrategy:
    def __init__(self, relevant_games):
        self._relevant_games = relevant_games
        self.last_input = None

    def select_games(self, games):
        self.last_input = games
        return list(self._relevant_games)


class FakeSteamSpyClient:
    def __init__(self, appid_to_tags, raise_for_appids=None):
        self._appid_to_tags = dict(appid_to_tags)
        self._raise_for = set(raise_for_appids or [])
        self.calls = []
        self._lock = threading.Lock()

    def get_top_tags(self, appid, num_tags=5):
        with self._lock:
            self.calls.append((str(appid), int(num_tags)))
        if str(appid) in self._raise_for:
            raise RuntimeError("steamspy error")
        return list(self._appid_to_tags.get(str(appid), []))[: int(num_tags)]


def test_build_top_tags_profile_returns_empty_when_no_relevant_games():
    steamspy = FakeSteamSpyClient({"1": ["a"]})
    strategy = FakeRelevantGamesStrategy(relevant_games=[])
    svc = TagProfileService(steamspy, strategy)

    top_tags, relevant = svc.build_top_tags_profile(owned_games=[{"appid": "1"}])

    assert relevant == []
    assert top_tags == []
    assert steamspy.calls == []


def test_build_top_tags_profile_counts_and_sorts_tags_with_tie_breaker():
    owned_games = [{"appid": "1"}, {"appid": "2"}, {"appid": "3"}]
    relevant_games = owned_games

    # counts: a=2, b=1, c=1. tie for b/c resolved alphabetically => b then c
    steamspy = FakeSteamSpyClient(
        {
            "1": ["b", "a"],
            "2": ["a", "c"],
            "3": [],
        }
    )
    strategy = FakeRelevantGamesStrategy(relevant_games=relevant_games)
    svc = TagProfileService(steamspy, strategy)

    top_tags, relevant = svc.build_top_tags_profile(
        owned_games=owned_games,
        top_tags_count=2,
        steamspy_tags_per_game=5,
    )

    assert relevant == relevant_games
    assert top_tags == ["a", "b"]


def test_build_top_tags_profile_passes_steamspy_tags_per_game_to_client():
    owned_games = [{"appid": "10"}]
    steamspy = FakeSteamSpyClient({"10": ["x", "y", "z"]})
    strategy = FakeRelevantGamesStrategy(relevant_games=owned_games)
    svc = TagProfileService(steamspy, strategy)

    top_tags, _relevant = svc.build_top_tags_profile(
        owned_games=owned_games,
        top_tags_count=5,
        steamspy_tags_per_game=2,
    )

    assert steamspy.calls == [("10", 2)]
    assert top_tags == ["x", "y"]


def test_build_top_tags_profile_ignores_exceptions_from_steamspy_client():
    owned_games = [{"appid": "1"}, {"appid": "2"}]

    steamspy = FakeSteamSpyClient({"1": ["a"]}, raise_for_appids={"2"})
    strategy = FakeRelevantGamesStrategy(relevant_games=owned_games)
    svc = TagProfileService(steamspy, strategy)

    top_tags, relevant = svc.build_top_tags_profile(owned_games=owned_games, top_tags_count=5)

    assert relevant == owned_games
    assert top_tags == ["a"]


def test_build_top_tags_profile_returns_empty_when_all_tags_empty():
    owned_games = [{"appid": "1"}, {"appid": "2"}]

    steamspy = FakeSteamSpyClient({"1": [], "2": []})
    strategy = FakeRelevantGamesStrategy(relevant_games=owned_games)
    svc = TagProfileService(steamspy, strategy)

    top_tags, _relevant = svc.build_top_tags_profile(owned_games=owned_games)

    assert top_tags == []
