from __future__ import annotations

import pytest

from app.services.steam_library_service import SteamLibraryService


class FakeSteamApiClient:
    def __init__(self):
        self.calls = []
        self._owned_games = []
        self._achievements = []
        self._global_percs = {}
        self.raise_on_achievements = None
        self.raise_on_global = None

    def get_owned_games(self, steam_id: str):
        self.calls.append(("get_owned_games", steam_id))
        return list(self._owned_games)

    def get_player_achievements(self, steam_id: str, appid: str):
        self.calls.append(("get_player_achievements", steam_id, appid))
        if self.raise_on_achievements:
            raise self.raise_on_achievements
        return list(self._achievements)

    def get_global_achievement_percentages(self, appid: str):
        self.calls.append(("get_global_achievement_percentages", appid))
        if self.raise_on_global:
            raise self.raise_on_global
        return dict(self._global_percs)


def test_get_owned_games_delegates_to_client():
    client = FakeSteamApiClient()
    client._owned_games = [{"appid": "1"}]

    svc = SteamLibraryService(client)
    assert svc.get_owned_games("steam123") == [{"appid": "1"}]
    assert ("get_owned_games", "steam123") in client.calls


def test_get_game_achievements_returns_none_when_no_achievements():
    client = FakeSteamApiClient()
    client._achievements = []

    svc = SteamLibraryService(client)
    assert svc.get_game_achievements("steam123", {"appid": "10", "name": "G"}) is None


def test_get_game_achievements_computes_percentage_and_rarest_icons_and_limits_to_3():
    client = FakeSteamApiClient()
    client._achievements = [
        {"apiname": "a1", "achieved": 1, "name": "A1", "description": "d1"},
        {"apiname": "a2", "achieved": 1, "name": "A2", "description": "d2"},
        {"apiname": "a3", "achieved": 1, "name": "A3", "description": "d3"},
        {"apiname": "a4", "achieved": 1, "name": "A4", "description": "d4"},
        {"apiname": "a5", "achieved": 0, "name": "A5", "description": "d5"},
    ]
    client._global_percs = {
        "a1": 10.0,   # plata
        "a2": 3.2,    # oro
        "a3": 40.0,   # bronce
        # a4 missing => default 100.0
    }

    svc = SteamLibraryService(client)
    result = svc.get_game_achievements("steam123", {"appid": "10", "name": "Game"})

    assert result["game_name"] == "Game"
    # total = 5, obtained = 4 => round(4/5*100) = 80
    assert result["percentage"] == 80
    assert result["total_obtained"] == 4
    assert result["total"] == 5

    rarest = result["rarest"]
    assert len(rarest) == 3
    # Sorted by global_percent ascending
    assert [r["name"] for r in rarest] == ["A2", "A1", "A3"]
    assert [r["icon"] for r in rarest] == ["oro.png", "plata.png", "bronce.png"]
    assert rarest[0]["global_percent"] == 3.2


def test_get_game_achievements_falls_back_to_apiname_and_default_description():
    client = FakeSteamApiClient()
    client._achievements = [
        {"apiname": "x", "achieved": 1},
        {"apiname": "y", "achieved": 0},
    ]
    client._global_percs = {"x": 99.9}

    svc = SteamLibraryService(client)
    result = svc.get_game_achievements("steam123", {"appid": "10"})

    assert result["game_name"] == "Sin nombre"
    assert result["percentage"] == 50
    assert result["rarest"][0]["name"] == "x"
    assert result["rarest"][0]["description"] == "Sin descripción"
    assert result["rarest"][0]["icon"] is None


def test_get_game_achievements_returns_none_on_client_exception(capsys):
    client = FakeSteamApiClient()
    client.raise_on_achievements = RuntimeError("boom")

    svc = SteamLibraryService(client)
    assert svc.get_game_achievements("steam123", {"appid": "10", "name": "G"}) is None


def test_get_game_achievements_returns_none_when_global_percentages_fail():
    client = FakeSteamApiClient()
    client._achievements = [{"apiname": "a", "achieved": 1, "name": "A"}]
    client.raise_on_global = RuntimeError("boom")

    svc = SteamLibraryService(client)
    assert svc.get_game_achievements("steam123", {"appid": "10", "name": "G"}) is None
