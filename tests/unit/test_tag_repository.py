from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.repositories.tag_repository import TagRepository


pytestmark = pytest.mark.unit


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_load_games_by_tag_returns_empty_list_when_file_missing(tmp_path: Path):
    repo = TagRepository(tags_dir=str(tmp_path))

    assert repo.load_games_by_tag("action") == []


def test_load_games_by_tag_loads_games_from_valid_json(tmp_path: Path):
    tags_dir = tmp_path / "tags"
    _write_json(
        tags_dir / "action.json",
        [
            {"appid": 10, "name": "Game A", "positive": 123, "relevancia": 0.7},
            {"appid": "20", "name": " Game B ", "positive": "5", "relevancia": "0.2"},
        ],
    )

    repo = TagRepository(tags_dir=str(tags_dir))
    games = repo.load_games_by_tag("action")

    assert games == [
        {"appid": "10", "name": "Game A", "positive": 123, "relevancia": 0.7},
        {"appid": "20", "name": "Game B", "positive": 5, "relevancia": 0.2},
    ]


def test_load_games_by_tag_returns_expected_fields_if_present_in_json(tmp_path: Path):
    tags_dir = tmp_path / "tags"
    _write_json(
        tags_dir / "rpg.json",
        [{"appid": "1", "name": "X", "positive": 9, "relevancia": 0.9, "extra": "ignored"}],
    )

    repo = TagRepository(tags_dir=str(tags_dir))
    game = repo.load_games_by_tag("rpg")[0]

    assert set(game.keys()) == {"appid", "name", "positive", "relevancia"}


def test_load_games_by_tag_handles_tags_with_spaces_and_special_characters(tmp_path: Path):
    tags_dir = tmp_path / "tags"

    # normalize_tag_to_filename: "Action RPG" -> "action_rpg"
    _write_json(
        tags_dir / "action_rpg.json",
        [{"appid": "1", "name": "X", "positive": 1, "relevancia": 0.1}],
    )

    repo = TagRepository(tags_dir=str(tags_dir))
    games = repo.load_games_by_tag(" Action RPG ")

    assert len(games) == 1
    assert games[0]["appid"] == "1"


def test_load_games_by_tag_returns_empty_list_for_empty_json_list(tmp_path: Path):
    tags_dir = tmp_path / "tags"
    _write_json(tags_dir / "empty.json", [])

    repo = TagRepository(tags_dir=str(tags_dir))
    assert repo.load_games_by_tag("empty") == []


def test_load_games_by_tag_returns_empty_list_when_json_is_empty_object(tmp_path: Path):
    tags_dir = tmp_path / "tags"
    _write_json(tags_dir / "weird.json", {})

    repo = TagRepository(tags_dir=str(tags_dir))
    assert repo.load_games_by_tag("weird") == []


def test_load_games_by_tag_handles_invalid_json_safely(tmp_path: Path):
    tags_dir = tmp_path / "tags"
    path = tags_dir / "bad.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json", encoding="utf-8")

    repo = TagRepository(tags_dir=str(tags_dir))
    assert repo.load_games_by_tag("bad") == []
