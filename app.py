import os
import re
import math
import json
import argparse
import csv
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

PORT = int(os.environ.get('PORT', 3000))
STEAM_API_KEY = os.environ.get('STEAM_API_KEY', 'TU_API_KEY_AQUI')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TAGS_DIR = os.path.join(BASE_DIR, 'tags')
APP_LIST_PATH = os.path.join(BASE_DIR, 'Steam_API', 'data', 'app_list.csv')
STEAM_API_BASE_URL = 'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/'
STEAMSPY_URL = 'https://steamspy.com/api.php'

steamSpyCache = {}
tagFileCache = {}
app_name_to_id_cache = {}
app_list_cache = []
app_list_loaded = False

def load_app_list():
    global app_list_loaded
    if not app_list_loaded:
        app_list_loaded = True
        try:
            with open(APP_LIST_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 2:
                        appid, game_name = row[0], row[1]
                        app_name_to_id_cache[game_name.strip().lower()] = appid
                        app_list_cache.append({'id': appid, 'name': game_name.strip()})
        except Exception as e:
            print(f"Error loading app_list.csv: {e}")

def get_appid_by_name(name):
    load_app_list()
    return app_name_to_id_cache.get(name.strip().lower())

@app.route('/api/search_games')
def api_search_games():
    q = request.args.get('q', '').strip().lower()
    if len(q) < 2:
        return jsonify([])
    
    load_app_list()
    results = []
    for game in app_list_cache:
        if q in game['name'].lower():
            results.append(game)
            if len(results) >= 15:
                break
    return jsonify(results)

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/opcion1')
@app.route('/opcion1.html')
def opcion1():
    return render_template('opcion1.html')

@app.route('/opcion2')
@app.route('/opcion2.html')
def opcion2():
    return render_template('opcion2.html')

@app.route('/api/recommend')
def api_recommend():
    steam_id = request.args.get('steamId', '').strip()
    if not re.match(r'^\d{17}$', steam_id):
        return jsonify({'error': 'El Steam ID debe ser un SteamID64 de 17 dígitos.'}), 400
    
    if STEAM_API_KEY == 'TU_API_KEY_AQUI':
        return jsonify({'error': 'Falta configurar la Steam API Key en app.py o en la variable de entorno STEAM_API_KEY.'}), 500
    
    try:
        owned_games = get_owned_games(steam_id, STEAM_API_KEY)
        if not owned_games:
            return jsonify({'error': 'No se ha podido leer la biblioteca. Revisa que el Steam ID sea correcto y que el perfil/juegos sean públicos.'}), 404
        
        relevant_games = get_relevant_games(owned_games)
        tag_counter = collect_frequent_tags(relevant_games, 5)
        top_tags = get_top_tags(tag_counter, 5)

        if not top_tags:
            return jsonify({'error': 'No se pudieron obtener tags suficientes desde SteamSpy para generar recomendaciones.'}), 404
        
        recommendations, missing_tag_files = recommend_games_from_local_tags(owned_games, top_tags, TAGS_DIR, limit=5)
        
        return jsonify({
            'steamId': steam_id,
            'topTags': top_tags,
            'missingTagFiles': missing_tag_files,
            'recommendations': recommendations,
            'stats': {
                'totalOwnedGames': len(owned_games),
                'relevantGamesAnalyzed': len(relevant_games)
            }
        })

    except requests.RequestException as e:
        print(f"Error en /api/recommend (API request): {e}")
        return jsonify({'error': f'Error de red: {e}'}), 500
    except Exception as e:
        print(f"Error en /api/recommend: {e}")
        return jsonify({'error': 'Ha ocurrido un error interno al generar las recomendaciones.'}), 500

@app.route('/api/recommend_by_game')
def api_recommend_by_game():
    app_id_or_name = request.args.get('appId', '').strip()
    if not app_id_or_name:
        return jsonify({'error': 'El App ID o Nombre no puede estar vacío.'}), 400
    
    app_id = app_id_or_name
    if not app_id.isdigit():
        resolved_id = get_appid_by_name(app_id_or_name)
        if not resolved_id:
            return jsonify({'error': f'No se encontró ningún juego con el nombre "{app_id_or_name}". Asegúrate de escribirlo exactamente o usa el App ID numérico.'}), 404
        app_id = resolved_id
    
    try:
        tags = get_steamspy_tags(app_id, 5)
        
        if not tags:
            return jsonify({'error': 'No se pudieron obtener tags suficientes desde SteamSpy para generar recomendaciones.'}), 404
        
        # Pass the input game as "owned" so it doesn't recommend the exact same game it was queried for
        owned_games = [{'appid': app_id}]
        recommendations, missing_tag_files = recommend_games_from_local_tags(owned_games, top_tags=tags, tags_dir=TAGS_DIR, limit=5)
        
        return jsonify({
            'appId': app_id,
            'topTags': tags,
            'missingTagFiles': missing_tag_files,
            'recommendations': recommendations
        })

    except requests.RequestException as e:
        print(f"Error en /api/recommend_by_game (API request): {e}")
        return jsonify({'error': f'Error de red: {e}'}), 500
    except Exception as e:
        print(f"Error en /api/recommend_by_game: {e}")
        return jsonify({'error': 'Ha ocurrido un error interno al generar las recomendaciones.'}), 500

def get_owned_games(steam_id, api_key):
    params = {
        'key': api_key,
        'steamid': steam_id,
        'include_appinfo': 'true',
        'include_played_free_games': 'true',
        'format': 'json'
    }
    resp = requests.get(STEAM_API_BASE_URL, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    games = data.get('response', {}).get('games', [])
    
    return [
        {
            'appid': str(game.get('appid', '')),
            'name': game.get('name') or 'Sin nombre',
            'playtime_forever': int(game.get('playtime_forever', 0)),
            'playtime_2weeks': int(game.get('playtime_2weeks', 0)),
            'img_icon_url': game.get('img_icon_url', ''),
            'img_logo_url': game.get('img_logo_url', ''),
            'has_community_visible_stats': bool(game.get('has_community_visible_stats', False))
        }
        for game in games
    ]

def get_relevant_games(games):
    if not games:
        return []
    sorted_games = sorted(games, key=lambda x: x['playtime_forever'], reverse=True)
    if len(sorted_games) < 30:
        return sorted_games
    amount = math.ceil(len(sorted_games) * 0.3)
    return sorted_games[:amount]

def collect_frequent_tags(games, tags_per_game=5):
    counter = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(get_steamspy_tags, game['appid'], tags_per_game): game for game in games}
        for future in as_completed(futures):
            tags = future.result()
            for tag in tags:
                counter[tag] = counter.get(tag, 0) + 1
    return counter

def get_steamspy_tags(appid, num_tags=5):
    cache_key = f"{appid}:{num_tags}"
    if cache_key in steamSpyCache:
        return steamSpyCache[cache_key]
    
    try:
        resp = requests.get(STEAMSPY_URL, params={'request': 'appdetails', 'appid': appid}, timeout=15)
        if not resp.ok:
            steamSpyCache[cache_key] = []
            return []
        
        data = resp.json()
        tags_object = data.get('tags')
        
        if not tags_object or not isinstance(tags_object, dict):
            steamSpyCache[cache_key] = []
            return []
        
        tags_sorted = sorted(tags_object.items(), key=lambda x: int(x[1]), reverse=True)
        tags = [str(k).lower() for k, v in tags_sorted[:num_tags]]
        
        steamSpyCache[cache_key] = tags
        return tags
    except Exception:
        steamSpyCache[cache_key] = []
        return []

def get_top_tags(counter, top_n=5):
    sorted_items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, v in sorted_items[:top_n]]

def normalize_tag_to_file_name(tag):
    tag = unicodedata.normalize('NFD', tag.strip().lower())
    tag = ''.join(c for c in tag if unicodedata.category(c) != 'Mn')
    tag = tag.replace('&', 'and')
    tag = re.sub(r'[ \-]+', '_', tag)
    tag = re.sub(r'[^a-z0-9_]', '', tag)
    tag = re.sub(r'_+', '_', tag)
    return tag.strip('_')

def load_tag_games(tag, tags_dir):
    file_name = f"{normalize_tag_to_file_name(tag)}.json"
    file_path = os.path.join(tags_dir, file_name)
    
    if file_path in tagFileCache:
        return tagFileCache[file_path]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            parsed = json.load(f)
            games = parsed if isinstance(parsed, list) else []
            tagFileCache[file_path] = games
            return games
    except Exception:
        tagFileCache[file_path] = []
        return []

def recommend_games_from_local_tags(owned_games, top_tags, tags_dir, limit=5):
    owned_ids = {str(g['appid']) for g in owned_games}
    candidates = {}
    missing_tag_files = []
    
    for tag in top_tags:
        tag_games = load_tag_games(tag, tags_dir)
        if not tag_games:
            missing_tag_files.append(tag)
            continue
        
        for game in tag_games:
            appid = str(game.get('appid', '')).strip()
            if not appid or appid in owned_ids:
                continue
            
            name = game.get('name', 'Sin nombre')
            positive = int(game.get('positive', 0))
            relevancia = float(game.get('relevancia', 0))
            
            if appid not in candidates:
                candidates[appid] = {
                    'appid': appid,
                    'name': name,
                    'positive': positive,
                    'coincidencias': 0,
                    'tagsCoincidentes': set(),
                    'relevancia_total': 0,
                    'relevancia_max': 0
                }
            
            c = candidates[appid]
            c['tagsCoincidentes'].add(tag)
            c['relevancia_total'] += relevancia
            c['relevancia_max'] = max(c['relevancia_max'], relevancia)
            c['positive'] = max(c['positive'], positive)

    recommendations_list = []
    for c in candidates.values():
        tags_coincidentes = sorted(list(c['tagsCoincidentes']))
        rec = {
            **c,
            'coincidencias': len(tags_coincidentes),
            'tagsCoincidentes': tags_coincidentes,
            'steamUrl': f"https://store.steampowered.com/app/{c['appid']}/"
        }
        recommendations_list.append(rec)
    
    recommendations_list.sort(key=lambda x: (
        -x['coincidencias'],
        -x['relevancia_total'],
        -x['relevancia_max'],
        -x['positive'],
        x['name'].lower()
    ))
    
    return recommendations_list[:limit], missing_tag_files

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Recomendador Steam Flask App")
    parser.add_argument('--steam-api-key', type=str, help='Tu Steam API Key (sobrescribe la variable de entorno)', default='428BA0E899DAECC321FF9CBBCE3540A6')
    parser.add_argument('--port', type=int, default=PORT, help='Puerto en el que se ejecutará el servidor')
    args = parser.parse_args()
    
    if args.steam_api_key:
        STEAM_API_KEY = args.steam_api_key
        
    app.run(host='0.0.0.0', port=args.port, debug=True)
