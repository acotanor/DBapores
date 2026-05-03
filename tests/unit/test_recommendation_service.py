from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.recommendation_service import RecommendationService


class FakeTagRepository:
    def __init__(self, tag_to_games: dict[str, list[dict]]):
        self._tag_to_games = tag_to_games

    def load_games_by_tag(self, tag: str) -> list[dict]:
        return list(self._tag_to_games.get(tag, []))


class FakeSortStrategy:
    def sort(self, candidates: list[dict]) -> list[dict]:
        # Keep the input order to make assertions deterministic.
        return list(candidates)


def _game(appid: str, name: str, positive: int = 1, relevancia: float = 0.5) -> dict:
    return {
        "appid": appid,
        "name": name,
        "positive": positive,
        "relevancia": relevancia,
    }


def _write_sponsored_json(path: Path, sponsored_appids: list[str]) -> str:
    path.write_text(json.dumps({"sponsored_appids": sponsored_appids}), encoding="utf-8")
    return str(path)


def test_recommend_from_tags_does_not_recommend_owned_games():
    repo = FakeTagRepository({
        "action": [
            _game("10", "Owned Game", positive=10, relevancia=0.9),
            _game("20", "New Game", positive=20, relevancia=0.9),
        ]
    })
    svc = RecommendationService(repo, FakeSortStrategy())

    owned_games = [{"appid": "10"}]
    recs, missing = svc.recommend_from_tags(owned_games=owned_games, top_tags=["action"], limit=10)

    assert missing == []
    assert [r["appid"] for r in recs] == ["20"]


def test_recommend_from_tags_accumulates_matching_tags_and_sorts_them():
    # Ensure tag list output is sorted alphabetically, regardless of input order.
    repo = FakeTagRepository({
        "tag_b": [_game("30", "Candidate", positive=10, relevancia=0.4)],
        "tag_a": [_game("30", "Candidate", positive=10, relevancia=0.7)],
    })
    svc = RecommendationService(repo, FakeSortStrategy())

    recs, missing = svc.recommend_from_tags(
        owned_games=[],
        top_tags=["tag_b", "tag_a"],
        limit=10,
    )

    assert missing == []
    assert len(recs) == 1
    assert recs[0]["tagsCoincidentes"] == ["tag_a", "tag_b"]
    assert recs[0]["coincidencias"] == 2


def test_recommend_from_tags_registers_missing_tag_files_when_no_data():
    repo = FakeTagRepository({
        "has_data": [_game("1", "One", positive=1, relevancia=0.5)],
        "no_data": [],
    })
    svc = RecommendationService(repo, FakeSortStrategy())

    recs, missing = svc.recommend_from_tags(
        owned_games=[],
        top_tags=["no_data", "has_data"],
        limit=10,
    )

    assert [r["appid"] for r in recs] == ["1"]
    assert missing == ["no_data"]


def test_recommend_from_tags_generates_steam_url():
    repo = FakeTagRepository({"t": [_game("999", "X", positive=1, relevancia=0.5)]})
    svc = RecommendationService(repo, FakeSortStrategy())

    recs, _missing = svc.recommend_from_tags(owned_games=[], top_tags=["t"], limit=10)

    assert recs[0]["steamUrl"] == "https://store.steampowered.com/app/999/"


def test_boost_applied_only_when_sponsored_and_relevancia_max_ge_0_6(tmp_path: Path):
    sponsored_path = _write_sponsored_json(tmp_path / "sponsored.json", ["100", "200"])

    repo = FakeTagRepository({
        "t": [
            _game("100", "Sponsored High", positive=1, relevancia=0.6),
            _game("200", "Sponsored Low", positive=1, relevancia=0.59),
        ]
    })
    svc = RecommendationService(repo, FakeSortStrategy(), sponsored_path=sponsored_path)

    recs, _missing = svc.recommend_from_tags(owned_games=[], top_tags=["t"], limit=10)
    by_id = {r["appid"]: r for r in recs}

    assert by_id["100"]["is_sponsored"] is True
    assert by_id["100"]["coincidencias"] == 101  # 1 tag + 100 boost

    assert by_id["200"]["is_sponsored"] is True
    assert by_id["200"]["coincidencias"] == 1  # no boost


def test_boost_not_applied_when_relevancia_low_even_if_sponsored(tmp_path: Path):
    sponsored_path = _write_sponsored_json(tmp_path / "sponsored.json", ["300"])

    repo = FakeTagRepository({"t": [_game("300", "Sponsored", positive=1, relevancia=0.1)]})
    svc = RecommendationService(repo, FakeSortStrategy(), sponsored_path=sponsored_path)

    recs, _missing = svc.recommend_from_tags(owned_games=[], top_tags=["t"], limit=10)

    assert recs[0]["is_sponsored"] is True
    assert recs[0]["coincidencias"] == 1


def test_boost_not_applied_when_not_sponsored_even_if_relevancia_high(tmp_path: Path):
    # sponsored list doesn't include the candidate
    sponsored_path = _write_sponsored_json(tmp_path / "sponsored.json", ["9999"])

    repo = FakeTagRepository({"t": [_game("400", "Not Sponsored", positive=1, relevancia=0.9)]})
    svc = RecommendationService(repo, FakeSortStrategy(), sponsored_path=sponsored_path)

    recs, _missing = svc.recommend_from_tags(owned_games=[], top_tags=["t"], limit=10)

    assert recs[0]["is_sponsored"] is False
    assert recs[0]["coincidencias"] == 1


def test_recommend_from_tags_respects_limit():
    repo = FakeTagRepository({
        "t": [
            _game("1", "A", positive=1, relevancia=0.5),
            _game("2", "B", positive=1, relevancia=0.5),
            _game("3", "C", positive=1, relevancia=0.5),
        ]
    })
    svc = RecommendationService(repo, FakeSortStrategy())

    recs, _missing = svc.recommend_from_tags(owned_games=[], top_tags=["t"], limit=2)

    assert len(recs) == 2
    assert [r["appid"] for r in recs] == ["1", "2"]
