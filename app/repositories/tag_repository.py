import json
import os
from app.adapters.tag_game_adapter import TagGameAdapter
from app.utils.text_utils import normalize_tag_to_filename


class TagRepository:
    def __init__(self, tags_dir: str):
        self.tags_dir = tags_dir
        self._cache = {}

    def load_games_by_tag(self, tag: str) -> list[dict]:
        filename = f"{normalize_tag_to_filename(tag)}.json"
        filepath = os.path.join(self.tags_dir, filename)

        if filepath in self._cache:
            return self._cache[filepath]

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                raw_data = json.load(file)

            games = raw_data if isinstance(raw_data, list) else []
            adapted = [TagGameAdapter.adapt(item) for item in games]
            self._cache[filepath] = adapted
            return adapted
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._cache[filepath] = []
            return []