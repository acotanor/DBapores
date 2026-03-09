import requests
from lista_juegos import ListaJuegos

BASE_URL = "https://api.steampowered.com/"
API_KEY = "428BA0E899DAECC321FF9CBBCE3540A6"


def resolve_vanity_url(vanity_name, key):
    url = f"{BASE_URL}ISteamUser/ResolveVanityURL/v1/"
    params = {
        "key": key,
        "vanityurl": vanity_name,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        resp = data.get("response", {})
        if resp.get("success") == 1:
            return resp.get("steamid")

        print("No se pudo resolver la vanity URL.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error al resolver vanity URL: {e}")
        return None


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


if __name__ == "__main__":
    steam_id = "76561199116601828"
    # vanity_name = "GabeNewell"
    # steam_id = resolve_vanity_url(vanity_name, API_KEY)

    if API_KEY == "TU_API_KEY_AQUI":
        print("Debes sustituir TU_API_KEY_AQUI por tu API key real.")
    elif not steam_id:
        print("No se ha podido obtener un SteamID válido.")
    else:
        lista_juegos = crear_lista_juegos_desde_steam(steam_id, API_KEY)
        print(lista_juegos)
        lista_juegos.mostrar_por_consola()