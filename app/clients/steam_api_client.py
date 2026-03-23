import requests


class SteamApiClient:
    def __init__(self, api_key: str, base_url: str, timeout: int = 15):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def get_owned_games(self, steam_id: str) -> list[dict]:
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "include_appinfo": "true",
            "include_played_free_games": "true",
            "format": "json",
        }

        response = requests.get(self.base_url, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        games = data.get("response", {}).get("games", [])

        return [
            {
                "appid": str(game.get("appid", "")),
                "name": game.get("name", "Sin nombre"),
                "playtime_forever": int(game.get("playtime_forever", 0)),
                "playtime_2weeks": int(game.get("playtime_2weeks", 0)),
                "img_icon_url": game.get("img_icon_url", ""),
                "img_logo_url": game.get("img_logo_url", ""),
                "has_community_visible_stats": bool(game.get("has_community_visible_stats", False)),
            }
            for game in games
        ]