import json
import sys
from pathlib import Path

import pytest
import requests

# Ensure the project root (parent of ./tests) is on sys.path even when pytest
# is executed from a different working directory.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app import create_app


@pytest.fixture(autouse=True)
def _block_external_http_requests(monkeypatch):
    """Safety net: tests must run offline; mock requests.get explicitly when needed."""

    def _blocked(*_args, **_kwargs):
        raise RuntimeError(
            "External HTTP requests are disabled in tests. "
            "Mock/monkeypatch requests.get (or the client methods) instead."
        )

    monkeypatch.setattr(requests, "get", _blocked)


@pytest.fixture()
def app(tmp_path: Path):
    flask_app = create_app()

    tags_dir = tmp_path / "tags"
    cache_dir = tmp_path / "cache"
    tags_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    app_list = tmp_path / "app_list.csv"
    app_list.write_text("appid,name\n", encoding="utf-8")

    sponsored = tmp_path / "sponsored_apps.json"
    sponsored.write_text(json.dumps({"sponsored_appids": []}), encoding="utf-8")

    flask_app.config.update(
        TESTING=True,
        STEAM_API_KEY="TEST_KEY",
        REQUEST_TIMEOUT=1,
        TAGS_DIR=str(tags_dir),
        CACHE_DIR=str(cache_dir),
        APP_LIST_PATH=str(app_list),
        SPONSORED_APPS_PATH=str(sponsored),
    )

    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()
