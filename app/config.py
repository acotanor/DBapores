import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    STEAM_API_KEY = os.getenv("STEAM_API_KEY", "TU_API_KEY_AQUI")
    TAGS_DIR = os.getenv("TAGS_DIR", "data/tags")
    CACHE_DIR = os.getenv("CACHE_DIR", "data/cache")
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))
    STEAM_API_BASE_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    STEAMSPY_URL = "https://steamspy.com/api.php"
    APP_LIST_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'data', 'app_list.csv')
    SPONSORED_APPS_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'data', 'sponsored_apps.json')