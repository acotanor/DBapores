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
            if not response.ok:
                print(f"DEBUG Client: SteamSpy API error for {appid}: HTTP {response.status_code}")
                self._cache[cache_key] = []
                return []

            data = response.json()
            if not data or not isinstance(data, dict):
                print(f"DEBUG Client: SteamSpy invalid JSON for {appid}")
                self._cache[cache_key] = []
                return []

            tags_obj = data.get("tags", {})
            if not isinstance(tags_obj, dict) or not tags_obj:
                print(f"DEBUG Client: No tags for {appid}. Checking genre.")
                genre_str = data.get('genre', '')
                if genre_str and isinstance(genre_str, str):
                    genres = [g.strip().lower() for g in genre_str.split(',') if g.strip()]
                    print(f"DEBUG Client: Using genre fallback for {appid}: {genres}")
                    tags = genres[:num_tags]
                    self._cache[cache_key] = tags
                    return tags
                
                self._cache[cache_key] = []
                return []

            # Robust sorting handling potential non-integer values
            try:
                tags = [
                    str(tag_name).lower()
                    for tag_name, _value in sorted(
                        tags_obj.items(),
                        key=lambda item: -int(str(item[1]).replace(',', '') if item[1] else 0)
                    )[:num_tags]
                ]
            except (ValueError, TypeError, KeyError) as e:
                print(f"DEBUG Client: Sorting error for {appid}: {e}")
                tags = [str(k).lower() for k in list(tags_obj.keys())[:num_tags]]

            self._cache[cache_key] = tags
            return tags
        except Exception as e:
            print(f"DEBUG Client: Exception for {appid}: {e}")
            self._cache[cache_key] = []
            return []