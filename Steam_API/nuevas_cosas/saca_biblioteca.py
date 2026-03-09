import requests
from lista_juegos import ListaJuegos

BASE_URL = "https://api.steampowered.com/"
API_KEY = "428BA0E899DAECC321FF9CBBCE3540A6"


def get_owned_games(steam_id, key):
    url = f"{BASE_URL}IPlayerService/GetOwnedGames/v1/"
    params = {
        "key": key,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("response", {}).get("games", [])
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la biblioteca: {e}")
        return []


def crear_lista_juegos_desde_steam(steam_id, key):
    games_data = get_owned_games(steam_id, key)
    lista_juegos = ListaJuegos.desde_api(games_data)
    lista_juegos.ordenar_por_tiempo_jugado()
    return lista_juegos