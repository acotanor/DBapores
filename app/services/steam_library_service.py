class SteamLibraryService:
    def __init__(self, steam_api_client):
        self.steam_api_client = steam_api_client

    def get_owned_games(self, steam_id: str) -> list[dict]:
        return self.steam_api_client.get_owned_games(steam_id)