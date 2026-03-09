import requests
import json
import os
import time
import collections
import math
import argparse

# Configuración extendida
OUTPUT_DIR = "tags"
CACHE_FILE = "top100_tags_cache.json"
TOP_TAGS_LIMIT = 30
MAX_GAMES_PER_TAG = 50  
VERIFY_LIMIT = 100      

def obtener_tags_juego(appid, silencioso=True, num_tags=5):
    """Consulta los tags de un juego específico en SteamSpy."""
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        datos = response.json()
        
        if 'tags' in datos and isinstance(datos['tags'], dict) and datos['tags']:
            tags_sorted = sorted(datos['tags'].items(), key=lambda x: x[1], reverse=True)
            
            if not silencioso:
                print(f"\nTags para {datos.get('name', appid)} (ID: {appid}):")
                for t, votos in tags_sorted[:20]:
                    print(f"- {t} ({votos} votos)")
            
            if num_tags is not None:
                return [t[0].lower() for t in tags_sorted[:num_tags]]
            else:
                return [t[0].lower() for t in tags_sorted]
        return []
    except Exception as e:
        if not silencioso: print(f"Error al obtener tags: {e}")
        return []

def generar_cache_top100(nombre_archivo=CACHE_FILE, num_tags=5):
    """Genera el JSON con el top 100 de juegos y sus tags principales."""
    url_top = "https://steamspy.com/api.php?request=top100in2weeks"
    print(f"Actualizando caché del Top 100 ({num_tags} tags/juego)...")
    
    try:
        response_top = requests.get(url_top)
        response_top.raise_for_status()
        top_100 = response_top.json()
        
        datos_guardar = {}
        total = len(top_100)
        
        for i, (appid, info) in enumerate(top_100.items(), 1):
            print(f"  > Procesando {i}/{total}: {info.get('name', '???')[:30]}...", end="\r")
            tags_juego = obtener_tags_juego(appid, silencioso=True, num_tags=num_tags)
            
            datos_guardar[appid] = {
                'name': info.get('name', 'Unknown'),
                'ccu': info.get('ccu', 0),
                'tags': tags_juego
            }
            time.sleep(0.2) # Pequeña pausa para no saturar
            
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos_guardar, f, ensure_ascii=False, indent=4)
            
        print(f"\n[OK] Caché guardada en {nombre_archivo}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Al generar caché: {e}")
        return False

def obtener_30_tags_frecuentes(archivo_cache=CACHE_FILE):
    """Identifica los 30 tags más comunes en el Top 100 de Steam."""
    if not os.path.exists(archivo_cache):
        return []
    
    with open(archivo_cache, "r", encoding="utf-8") as f:
        data = json.load(f)
        tags_raw = [t for g in data.values() for t in g.get('tags', [])]
        most_common = collections.Counter(tags_raw).most_common(TOP_TAGS_LIMIT)
        return [t[0] for t in most_common]

def calcular_peso_relevancia(tags_dict, tag_objetivo):
    """Calcula el peso (0.1 a 1.0) según el rank del tag en el juego."""
    ordenados = sorted(tags_dict.items(), key=lambda x: x[1], reverse=True)
    for rank, (tag, votos) in enumerate(ordenados[:10], 1):
        if tag.lower() == tag_objetivo.lower():
            return round(1.1 - (rank * 0.1), 1)
    return 0

def generar_cache_tags(tag, i, total):
    """Genera caché de relevancia con límites extendidos."""
    tag_query = tag.replace(' ', '+')
    url = f"https://steamspy.com/api.php?request=tag&tag={tag_query}"
    
    progreso = int((i / total) * 20)
    barra = "█" * progreso + "░" * (20 - progreso)
    porcentaje = round((i / total) * 100, 1)
    
    nombre_archivo = tag.lower().replace(' ', '_').replace('-', '_') + ".json"
    ruta_archivo = os.path.join(OUTPUT_DIR, nombre_archivo)
    accion = "[ACTUALIZANDO]" if os.path.exists(ruta_archivo) else "[CREANDO]"
    
    print(f"\n[{barra}] {porcentaje}% | {accion} Tag: {tag}")
    
    try:
        r = requests.get(url)
        juegos = r.json()
        if not juegos or not isinstance(juegos, dict): return
        
        juegos_populares = sorted(juegos.items(), key=lambda x: x[1].get('positive', 0), reverse=True)
        
        resultados = []
        analizados = 0
        for appid, info in juegos_populares:
            if analizados >= VERIFY_LIMIT or len(resultados) >= MAX_GAMES_PER_TAG:
                break
            
            print(f"  > Analizando profundidad: {info['name'][:30]}...", end="\r")
            
            # Consultar detalles para ver el ADN (rank del tag)
            url_detalles = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
            try:
                rd = requests.get(url_detalles)
                detalles = rd.json()
                if 'tags' in detalles and isinstance(detalles['tags'], dict):
                    peso = calcular_peso_relevancia(detalles['tags'], tag)
                    if peso > 0:
                        resultados.append({
                            'appid': appid,
                            'name': info['name'],
                            'positive': info.get('positive', 0),
                            'relevancia': peso
                        })
            except: pass
            
            analizados += 1
            time.sleep(0.4) # Respetar API
            
        if resultados:
            # Ordenación final balanceada para el JSON
            for res in resultados:
                res['_score'] = math.log10(max(2, res['positive'])) * res['relevancia']
            
            resultados = sorted(resultados, key=lambda x: x['_score'], reverse=True)
            for res in resultados: del res['_score']
            
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(resultados, f, indent=4, ensure_ascii=False)
            print(f"  [OK] Generados {len(resultados)} juegos para {tag}")

    except Exception as e:
        print(f"  [ERROR] {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de videojuegos por tags para DBapores")
    parser.add_argument("--refresh-cache", action="store_true", help="Fuerza la actualización de top100_tags_cache.json")
    parser.add_argument("--tags-per-game", type=int, default=5, help="Número de tags a guardar por juego en el caché (default: 5)")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Verificar/Generar Caché del Top 100
    if args.refresh_cache or not os.path.exists(CACHE_FILE):
        if not generar_cache_top100(num_tags=args.tags_per_game):
            print("Abortando: No se pudo generar el caché necesario.")
            exit(1)
    else:
        print(f"Usando caché existente: {CACHE_FILE}")

    # 2. Obtener los 30 tags más frecuentes
    tags = obtener_30_tags_frecuentes()
    if not tags:
        print("Error: No se encontraron tags en el caché. Intenta con --refresh-cache.")
        exit(1)

    print(f"Iniciando análisis de videojuegos para los {len(tags)} tags más frecuentes...")
    print(f"(Config: {MAX_GAMES_PER_TAG} juegos/tag, profundidad {VERIFY_LIMIT})")
    
    for i, tag in enumerate(tags, 1):
        generar_cache_tags(tag, i, len(tags))
    
    print(f"\n¡Proceso completado! Los archivos están en: {OUTPUT_DIR}/")
