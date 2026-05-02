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

    def get_player_achievements(self, steam_id: str, appid: str) -> list[dict]:
        url = "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/"
        params = {
            "key": self.api_key,
            "steamid": steam_id,
            "appid": appid,
            "l": "spanish"
        }
        response = requests.get(url, params=params, timeout=self.timeout)
        if not response.ok:
            return []
        
        data = response.json()
        return data.get("playerstats", {}).get("achievements", [])

    def get_global_achievement_percentages(self, appid: str) -> dict:
        url = "https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/"
        params = {"gameid": appid}
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            if not response.ok:
                return {}
            
            data = response.json()
            achs = data.get("achievementpercentages", {}).get("achievements", [])
            return {a['name']: float(a['percent']) for a in achs}
        except Exception:
            return {}