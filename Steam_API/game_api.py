import requests
import json

# La API de detalles de la tienda es distinta a la API de usuarios
STORE_URL = 'https://store.steampowered.com/api/appdetails'
BASE_URL = 'https://api.steampowered.com/'
API_KEY = '112E7CAE5268A96388B6FB4E3FDCFFB9'
ID = '76561198185726019'
user_vanity = "https://steamcommunity.com/id/GabeLoganNewell"
VAN_ID=''

def get_owned_games(steam_id, key):
    url = f"{BASE_URL}IPlayerService/GetOwnedGames/v1/"
    params = {
        'key': key,
        'steamid': steam_id,
        'include_appinfo': True,
        'format': 'json'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        # El resultado viene dentro de ['response']['games']
        return data.get('response', {}).get('games', [])
    except Exception as e:
        print(f"Error: {e}")
        return []
    
def get_game_details(app_id):
      params = {
           'appids': app_id,
           'l': 'spanish'
      }
      try:
        response = requests.get(STORE_URL, params=params)
        response.raise_for_status() # Lanza error si es 4xx o 5xx
        
        data = response.json()
        
        # Steam devuelve { "appid": { "success": True/False, "data": {...} } }
        if data and str(app_id) in data and data[str(app_id)]['success']:
            return data[str(app_id)]['data']
        else:
            print(f"ID {app_id} no encontrado o sin datos públicos.")
            return None
      except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return None

if __name__ == '__main__':
    #APP_ID= 730 # Counter Strike 2
    APP_ID = 250900 # The Binding of Isaac: Rebirth
    
    game_data = get_game_details(APP_ID)
    games = get_owned_games(ID, API_KEY)
    
    if game_data:
        print(f"Nombre: {game_data['name']}")
        print(f"Descripción corta: {game_data['short_description'][:100]}...\n")
        # Descomenta para ver todo el JSON:
        #print(json.dumps(game_data, indent=2, ensure_ascii=False))
    if games:
        # Ordenar por tiempo de juego (minutos) de mayor a menor
        games_sorted = sorted(games, key=lambda x: x['playtime_forever'], reverse=True)
        #print(games_sorted)

        print(f"{'Juego':<30} | {'Horas jugadas':<15} | {'AppId'}")
        print("-" * 60)
        for game in games_sorted[:10]: # Top 10
            hours = round(game['playtime_forever'] / 60, 1)
            print(f"{game['name'][:30]:<30} | {hours:<15} | {game['appid']}")

    