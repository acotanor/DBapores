import requests


class SteamSpyClient:
    def __init__(self, base_url: str, timeout: int = 15):
        self.base_url = base_url
        self.timeout = timeout
        self._cache = {}

    def get_top_tags(self, appid: str, num_tags: int = 5) -> list[str]:
        cache_key = f"{appid}:{num_tags}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            response = requests.get(
                self.base_url,
                params={"request": "appdetails", "appid": str(appid)},
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            tags_obj = data.get("tags", {})

            if not isinstance(tags_obj, dict):
                self._cache[cache_key] = []
                return []

            tags = [
                str(tag_name).lower()
                for tag_name, _value in sorted(
                    tags_obj.items(),
                    key=lambda item: -int(item[1])
                )[:num_tags]
            ]

            self._cache[cache_key] = tags
            return tags
        except Exception:
            self._cache[cache_key] = []
            return []