import os
import requests
import json
import time
import re
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('STEAM_API_KEY')
STEAM_ID = '76561198185726019'
ARCHIVO_DATOS = 'biblioteca_steam.json'

def cargar_cache():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_cache(datos):
    with open(ARCHIVO_DATOS, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

import re

def get_game_extra_info(appid, cache):
    if str(appid) in cache:
        return cache[str(appid)]

    #print(f"Consultando información completa para: {appid}...")
    info = {
        'nombre': "N/A",
        'genero': 'N/A', 
        'desarrollador': 'N/A', 
        'precio': 'N/A',
        'metacritic': 'N/A',
        'espacio_disco': 'N/A',
        'es_multiplayer': False,
        'tags': []
    }

    # 1. SteamSpy: Tags, Desarrollador y Género
    try:
        ss_url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
        ss_res = requests.get(ss_url).json()
        info['nombre'] = ss_res.get('name', 'N/A')
        info['desarrollador'] = ss_res.get('developer', 'N/A')
        info['genero'] = ss_res.get('genre', 'N/A')
        
        # Extraer los 5 tags con más votos
        tags_dict = ss_res.get('tags', {})
        if tags_dict:
            # Ordenamos los tags por cantidad de votos (valor del dict)
            sorted_tags = sorted(tags_dict.items(), key=lambda x: x[1], reverse=True)
            info['tags'] = [tag[0] for tag in sorted_tags[:5]]
    except: pass

    # 2. Steam Store API: Precio, Metacritic, Espacio y Categorías
    try:
        store_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=spanish"
        store_res = requests.get(store_url).json()
        if store_res and store_res[str(appid)]['success']:
            data = store_res[str(appid)]['data']
            
            # Precio
            info['precio'] = data.get('price_overview', {}).get('final_formatted', 'Gratis/N/A')
            
            # Metacritic
            info['metacritic'] = data.get('metacritic', {}).get('score', 'N/A')
            
            # ¿Es Multiplayer? (Buscamos en categorías)
            categories = [c.get('description', '').lower() for c in data.get('categories', [])]
            info['es_multiplayer'] = any('multijugador' in cat or 'multiplayer' in cat for cat in categories)

            # Espacio en disco (Truco: buscamos "GB" o "MB" en requisitos mínimos)
            requirements = data.get('pc_requirements', {}).get('minimum', '')
            storage_match = re.search(r'(\d+)\s*(GB|MB)\s*de espacio', requirements, re.IGNORECASE)
            if storage_match:
                info['espacio_disco'] = f"{storage_match.group(1)} {storage_match.group(2)}"
    except: pass

    time.sleep(1.2)
    return info

def get_owned_games(steam_id, key):
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    params = {'key': key, 'steamid': steam_id, 'include_appinfo': True, 'format': 'json'}
    try:
        r = requests.get(url, params=params)
        return r.json().get('response', {}).get('games', [])
    except: return []

if __name__ == '__main__':
    cache = cargar_cache()
    games = get_owned_games(STEAM_ID, API_KEY)

    if games:
        # Top 15 juegos
        top_games = sorted(games, key=lambda x: x['playtime_forever'], reverse=True)[:15]
        
        print("\n" + "="*95)
        print(f"{'JUEGO':<35} | {'HORAS':<7} | {'META':<5} | {'PRECIO':<12} | {'ESPACIO'}")
        print("="*95)

        for game in top_games:
            appid = game['appid']
            extra = get_game_extra_info(appid, cache)
            cache[str(appid)] = extra
            
            hours = round(game['playtime_forever'] / 60, 1)
            
            # Formatear el nombre para que no rompa la tabla si es muy largo
            nombre = game['name'][:33] + ".." if len(game['name']) > 33 else game['name']
            
            # Fila principal
            print(f"{nombre:<35} | {hours:<7} | {extra['metacritic']:<5} | {extra['precio']:<12} | {extra['espacio_disco']}")
            
            # Fila de detalles (Tags y Multiplayer)
            multi = " [Multiplayer]" if extra['es_multiplayer'] else " [Solo]"
            tags_str = ", ".join(extra['tags'][:4]) # Mostramos los primeros 4 tags
            print(f"  └─ Tags: {tags_str:<50} {multi}")
            print("-" * 95)

        guardar_cache(cache)
        print(f"\n[OK] Datos actualizados y guardados en {ARCHIVO_DATOS}")
        
    else:
        print("No se encontraron juegos.")