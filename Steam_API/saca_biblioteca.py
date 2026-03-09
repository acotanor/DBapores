import requests

BASE_URL = "https://api.steampowered.com/"
API_KEY = "428BA0E899DAECC321FF9CBBCE3540A6"


def resolve_vanity_url(vanity_name, key):
    """
    Convierte una vanity URL de Steam (por ejemplo 'gaben') en un SteamID64.
    """
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
        else:
            print("No se pudo resolver la vanity URL.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error al resolver vanity URL: {e}")
        return None


def get_owned_games(steam_id, key):
    """
    Obtiene la biblioteca de juegos de un usuario.
    """
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


def imprimir_biblioteca(games, top=None):
    """
    Muestra la biblioteca ordenada por horas jugadas.
    """
    if not games:
        print("No se encontraron juegos en la biblioteca o el perfil no es público.")
        return

    games_sorted = sorted(games, key=lambda x: x.get("playtime_forever", 0), reverse=True)

    print(f"\nTotal de juegos encontrados: {len(games_sorted)}\n")
    print(f"{'Juego':<40} | {'Horas jugadas':<15} | {'AppID'}")
    print("-" * 75)

    lista = games_sorted[:top] if top is not None else games_sorted

    for game in lista:
        name = game.get("name", "Sin nombre")
        appid = game.get("appid", "N/A")
        hours = round(game.get("playtime_forever", 0) / 60, 1)
        print(f"{name[:40]:<40} | {hours:<15} | {appid}")


if __name__ == "__main__":
    # Opción 1: usar SteamID64 directamente
    steam_id = "76561199116601828"

    # Opción 2: usar vanity URL (descomenta si quieres usar nombre personalizado)
    # vanity_name = "GabeLoganNewell"
    # steam_id = resolve_vanity_url(vanity_name, API_KEY)

    if not API_KEY or API_KEY == "TU_API_KEY_AQUI":
        print("Debes poner tu API key de Steam en la variable API_KEY.")
    elif steam_id:
        games = get_owned_games(steam_id, API_KEY)
        imprimir_biblioteca(games, top=20)
    else:
        print("No se pudo obtener un SteamID válido.")