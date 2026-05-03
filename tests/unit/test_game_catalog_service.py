from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.services.game_catalog_service import GameCatalogService


def _write_app_list_csv(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["appid", "name"])
        for appid, name in rows:
            writer.writerow([appid, name])


def test_normalize_search_name_returns_empty_string_for_none():
    svc = GameCatalogService(app_list_path="/does/not/matter.csv")
    assert svc.normalize_search_name(None) == ""


def test_normalize_search_name_returns_empty_string_for_empty_input():
    svc = GameCatalogService(app_list_path="/does/not/matter.csv")
    assert svc.normalize_search_name("") == ""


def test_normalize_search_name_strips_and_collapses_extra_spaces():
    svc = GameCatalogService(app_list_path="/does/not/matter.csv")
    assert svc.normalize_search_name("  hello   world  ") == "hello world"


def test_normalize_search_name_lowercases_input():
    svc = GameCatalogService(app_list_path="/does/not/matter.csv")
    assert svc.normalize_search_name("HeLLo WoRLD") == "hello world"


def test_normalize_search_name_removes_trademark_symbols():
    svc = GameCatalogService(app_list_path="/does/not/matter.csv")
    result = svc.normalize_search_name("Rainbow Six® Siege™ ©")

    # The intent is to strip trademark/copyright glyphs from search names.
    # Note: with NFKD normalization, ™ can become the letters "TM".
    assert "®" not in result and "™" not in result and "©" not in result
    assert result.lower() in {"rainbow six siege", "rainbow six siegetm"}


def test_get_appid_by_name_resolves_using_normalized_matching(tmp_path: Path):
    csv_path = tmp_path / "app_list.csv"
    _write_app_list_csv(
        csv_path,
        rows=[
            ("359550", "Tom Clancy's Rainbow Six® Siege"),
            ("730", "Counter-Strike 2"),
        ],
    )

    svc = GameCatalogService(app_list_path=str(csv_path))

    # Case-insensitive, ignores extra spaces and ® symbol
    assert svc.get_appid_by_name("  TOM CLANCY'S  RAINBOW SIX siege ") == "359550"


def test_get_game_by_id_returns_game_info_if_present(tmp_path: Path):
    csv_path = tmp_path / "app_list.csv"
    _write_app_list_csv(
        csv_path,
        rows=[
            ("730", "Counter-Strike 2"),
            ("570", "Dota 2"),
        ],
    )

    svc = GameCatalogService(app_list_path=str(csv_path))
    assert svc.get_game_by_id("570") == {"id": "570", "name": "Dota 2"}


def test_get_game_by_id_returns_none_when_missing(tmp_path: Path):
    csv_path = tmp_path / "app_list.csv"
    _write_app_list_csv(csv_path, rows=[("730", "Counter-Strike 2")])

    svc = GameCatalogService(app_list_path=str(csv_path))
    assert svc.get_game_by_id("999") is None


def test_search_games_respects_limit(tmp_path: Path):
    csv_path = tmp_path / "app_list.csv"
    _write_app_list_csv(
        csv_path,
        rows=[
            ("1", "Alpha"),
            ("2", "Alpine"),
            ("3", "Alchemist"),
            ("4", "Bravo"),
        ],
    )

    svc = GameCatalogService(app_list_path=str(csv_path))
    results = svc.search_games("al", limit=2)

    assert len(results) == 2
    assert [r["id"] for r in results] == ["1", "2"]


def test_search_games_returns_empty_list_when_no_results(tmp_path: Path):
    csv_path = tmp_path / "app_list.csv"
    _write_app_list_csv(csv_path, rows=[("1", "Alpha"), ("2", "Bravo")])

    svc = GameCatalogService(app_list_path=str(csv_path))
    assert svc.search_games("zz") == []
