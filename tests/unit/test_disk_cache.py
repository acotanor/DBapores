from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.utils.disk_cache import DiskCache


pytestmark = pytest.mark.unit


def test_get_returns_none_when_key_missing(tmp_path: Path):
    cache = DiskCache(str(tmp_path))
    assert cache.get("missing") is None
    assert cache.has("missing") is False


def test_set_then_get_roundtrips_value(tmp_path: Path):
    cache = DiskCache(str(tmp_path))

    cache.set("k", {"a": 1, "b": [1, 2]})

    assert cache.has("k") is True
    assert cache.get("k") == {"a": 1, "b": [1, 2]}


def test_key_is_sanitized_to_safe_filename(tmp_path: Path):
    cache = DiskCache(str(tmp_path))

    cache.set("a/b c", 123)

    # '/' and spaces become '_' per implementation
    expected_file = tmp_path / "a_b_c.json"
    assert expected_file.exists()
    assert cache.get("a/b c") == 123


def test_get_returns_none_when_cached_file_contains_invalid_json(tmp_path: Path):
    cache = DiskCache(str(tmp_path))

    key = "bad"
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")

    assert cache.get(key) is None


def test_set_overwrites_existing_value(tmp_path: Path):
    cache = DiskCache(str(tmp_path))

    cache.set("k", {"v": 1})
    cache.set("k", {"v": 2})

    assert cache.get("k") == {"v": 2}
