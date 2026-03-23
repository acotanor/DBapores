import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    STEAM_API_KEY = os.getenv("STEAM_API_KEY", "TU_API_KEY_AQUI")
    TAGS_DIR = os.getenv("TAGS_DIR", "data/tags")
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
    STEAM_API_BASE_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    STEAMSPY_URL = "https://steamspy.com/api.php"