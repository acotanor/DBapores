from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "path",
    [
        "/api/recommend",  # missing steamId
        "/api/recommend?steamId=not-a-number",
        "/api/recommend?steamId=123",  # too short
    ],
)
def test_recommend_invalid_steamid_returns_400(client, path):
    resp = client.get(path)
    assert resp.status_code == 400
    data = resp.get_json()
    assert isinstance(data, dict)
    assert "error" in data


def test_recommend_steamid_non_numeric_returns_400(client):
    resp = client.get("/api/recommend?steamId=1234567890123456a")
    assert resp.status_code == 400


def test_recommend_steamid_short_returns_400(client):
    resp = client.get("/api/recommend?steamId=1234567890123")
    assert resp.status_code == 400


def test_recommend_with_unconfigured_api_key_returns_500(app, client):
    app.config["STEAM_API_KEY"] = "TU_API_KEY_AQUI"

    resp = client.get("/api/recommend?steamId=12345678901234567")
    assert resp.status_code == 500
    assert "error" in (resp.get_json() or {})


def test_recommend_with_mocked_facade_returns_200_and_expected_json(client, patch_build_facade):
    expected = {"steamId": "12345678901234567", "recommendations": [1, 2, 3]}

    class FakeFacade:
        def generate_recommendations(self, steam_id: str, limit: int, top_tags_count: int):
            assert steam_id == "12345678901234567"
            assert limit == 15
            assert top_tags_count == 5
            return expected

    patch_build_facade(FakeFacade())

    resp = client.get("/api/recommend?steamId=12345678901234567")
    assert resp.status_code == 200
    assert resp.get_json() == expected


def test_recommend_when_facade_raises_value_error_returns_404(client, patch_build_facade):
    class FakeFacade:
        def generate_recommendations(self, *args, **kwargs):
            raise ValueError("not found")

    patch_build_facade(FakeFacade())

    resp = client.get("/api/recommend?steamId=12345678901234567")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "not found"}


def test_recommend_when_facade_raises_exception_returns_500(client, patch_build_facade):
    class FakeFacade:
        def generate_recommendations(self, *args, **kwargs):
            raise Exception("boom")

    patch_build_facade(FakeFacade())

    resp = client.get("/api/recommend?steamId=12345678901234567")
    assert resp.status_code == 500
    assert resp.get_json() == {"error": "Error interno al generar las recomendaciones."}


def test_recommend_by_game_without_appid_returns_400(client):
    resp = client.get("/api/recommend_by_game")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data == {"error": "El App ID o Nombre no puede estar vacío."}


def test_recommend_by_game_with_mocked_facade_returns_200(client, patch_build_facade):
    expected = {"appId": "730", "topTags": ["fps"], "recommendations": [{"appid": "1"}]}

    class FakeFacade:
        def recommend_by_game(self, app_id_or_name: str, limit: int):
            assert app_id_or_name == "730"
            assert limit == 15
            return expected

    patch_build_facade(FakeFacade())

    resp = client.get("/api/recommend_by_game?appId=730")
    assert resp.status_code == 200
    assert resp.get_json() == expected


def test_recommend_by_game_when_facade_raises_value_error_returns_404(client, patch_build_facade):
    class FakeFacade:
        def recommend_by_game(self, *args, **kwargs):
            raise ValueError("missing game")

    patch_build_facade(FakeFacade())

    resp = client.get("/api/recommend_by_game?appId=does-not-matter")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "missing game"}


def test_wrapped_with_invalid_steam_id_returns_400(client):
    resp = client.get("/api/wrapped/not-a-steamid")
    assert resp.status_code == 400
    data = resp.get_json()
    assert isinstance(data, dict)
    assert "error" in data


def test_search_games_query_too_short_returns_empty_list(client):
    resp = client.get("/api/search_games?q=a")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_search_games_query_valid_returns_mocked_list(client, patch_build_facade):
    expected = [
        {"id": "1", "name": "Alpha"},
        {"id": "2", "name": "Alpine"},
    ]

    class FakeGameCatalogService:
        def search_games(self, q, limit=15):
            assert q == "al"
            return expected

    class FakeFacade:
        def __init__(self):
            self.game_catalog_service = FakeGameCatalogService()

    patch_build_facade(FakeFacade())

    resp = client.get("/api/search_games?q=al")
    assert resp.status_code == 200
    assert resp.get_json() == expected
