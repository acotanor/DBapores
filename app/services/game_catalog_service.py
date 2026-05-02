import csv
import re
import unicodedata
import os

class GameCatalogService:
    def __init__(self, app_list_path):
        self.app_list_path = app_list_path
        self._app_list_cache = []
        self._app_name_to_id_cache = {}
        self._app_list_loaded = False

    def normalize_search_name(self, name):
        """
        Strips symbols like ® and ™ to ensure robust matches.
        """
        if not name:
            return ""
        # NFKD normalization separates base characters from their marks.
        name = unicodedata.normalize('NFKD', name.strip().lower())
        # Remove registered trademark, trademark, and copyright symbols.
        name = re.sub(r'[®™©]', '', name)
        # Remove extra whitespace.
        return re.sub(r'\s+', ' ', name).strip()

    def _load_app_list(self):
        """Loads the CSV into memory caches for searching and name resolution."""
        if not self._app_list_loaded:
            self._app_list_loaded = True
            try:
                if not os.path.exists(self.app_list_path):
                    print(f"Error: app_list.csv not found at {self.app_list_path}")
                    return

                with open(self.app_list_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip CSV header
                    for row in reader:
                        if len(row) >= 2:
                            appid, game_name = row[0], row[1]
                            clean_name = self.normalize_search_name(game_name)
                            self._app_name_to_id_cache[clean_name] = appid
                            self._app_list_cache.append({'id': appid, 'name': game_name.strip()})
            except Exception as e:
                print(f"Error loading app_list.csv: {e}")

    def get_game_by_id(self, appid):
        """Returns game info from cache if available."""
        self._load_app_list()
        appid = str(appid)
        for g in self._app_list_cache:
            if g['id'] == appid:
                return g
        return None

    def get_appid_by_name(self, name):
        """Resolves a game name to its App ID using normalized matching."""
        self._load_app_list()
        return self._app_name_to_id_cache.get(self.normalize_search_name(name))

    def search_games(self, query, limit=15):
        """Filters the app list for search suggestions."""
        self._load_app_list()
        clean_q = self.normalize_search_name(query)
        results = []
        
        for game in self._app_list_cache:
            if clean_q in self.normalize_search_name(game['name']):
                results.append(game)
                if len(results) >= limit:
                    break
        return results
