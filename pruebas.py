import requests
import json
import os
import argparse

def obtener_shooters_por_genero():
    # El tag 'Shooter' en Steam tiene el ID '418' o el nombre 'Shooter'
    url = "https://steamspy.com/api.php?request=tag&tag=Shooter"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        datos = response.json()
        
        # SteamSpy devuelve un diccionario donde las llaves son los IDs de los juegos
        # Limitamos a los primeros 15 para no saturar la consola
        for i, (appid, info) in enumerate(datos.items()):
            if i >= 15: break
            print(f"{info['name']:<40} | {appid:<10} | {info['positive']:,}")
            
    except Exception as e:
        print(f"Error al conectar con SteamSpy: {e}")

def obtener_tags_juego(appid, silencioso=False, num_tags=5):
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        datos = response.json()
        
        if 'tags' in datos and isinstance(datos['tags'], dict) and datos['tags']:
            if not silencioso:
                print(f"\nTags para {datos['name']} (ID: {appid}):")
                
            tags_sorted = sorted(datos['tags'].items(), key=lambda x: x[1], reverse=True)
            
            if not silencioso:
                for t, votos in tags_sorted[:20]:
                    print(f"- {t} ({votos} votos)")
            
            # Devolvemos la lista de nombres de tags
            if num_tags is not None:
                return [t[0].lower() for t in tags_sorted[:num_tags]]
            else:
                return [t[0].lower() for t in tags_sorted]
        else:
            if not silencioso:
                print(f"No se encontraron tags para el AppID {appid}.")
            return []
            
    except Exception as e:
        if not silencioso:
            print(f"Error al obtener tags: {e}")
        return []

def obtener_recomendaciones(appid):
    # 1. Obtener los 5 tags más populares del juego base
    top_5_tags = obtener_tags_juego(appid, silencioso=True, num_tags=5)
    if not top_5_tags:
        print("No se encontraron tags para este juego.")
        return
        
    url_base = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    # ... resto del codigo ...
    try:
        resp = requests.get(url_base)
        datos_juego = resp.json()
        nombre_original = datos_juego['name']
        
        print(f"\nBuscando recomendaciones para '{nombre_original}' basadas en: {', '.join(top_5_tags)}")
        
        # 2. Buscar juegos para cada tag y contar coincidencias
        coincidencias = {} # {appid: {'count': N, 'name': 'Name'}}
        
        for tag in top_5_tags:
            # Reemplazar espacios por + para la URL
            tag_url = tag.replace(' ', '+')
            resp_tag = requests.get(f"https://steamspy.com/api.php?request=tag&tag={tag_url}")
            juegos_tag = resp_tag.json()
            
            # SteamSpy devuelve un dict de juegos para cada tag
            for aid, info in juegos_tag.items():
                if aid == str(appid): continue # Saltar el juego original
                
                if aid not in coincidencias:
                    coincidencias[aid] = {'count': 1, 'name': info['name']}
                else:
                    coincidencias[aid]['count'] += 1
        
        # 3. Filtrar y ordenar
        # Ordenar por número de coincidencias desc
        recomendados = sorted(coincidencias.values(), key=lambda x: x['count'], reverse=True)
        
        print(f"\n{'Juego Recomendado':<50} | {'Tags Coincidentes':<15}")
        print("-" * 70)
        
        # Mostramos los 10 mejores que tengan al menos 2 tags en común
        count = 0
        for j in recomendados:
            if j['count'] >= 2 and count < 10:
                print(f"{j['name']:<50} | {j['count']}/5")
                count += 1
            
    except Exception as e:
        print(f"Error al generar recomendaciones: {e}")

def obtener_top_100_en_2_semanas():
    url = "https://steamspy.com/api.php?request=top100in2weeks"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        datos = response.json()
        
        print("\nTop 100 juegos más jugados (últimas 2 semanas):")
        print(f"{'Ranking':<8} | {'Nombre':<40} | {'AppID':<10} | {'Current Players (CCU)':<25}")
        print("-" * 90)
        
        for i, (appid, info) in enumerate(datos.items(), 1):
            ccu = info.get('ccu', 'N/A')
            # Algunos nombres pueden ser largos, los cortamos a 39 caracteres
            nombre = info['name'][:39] 
            print(f"{i:<8} | {nombre:<40} | {appid:<10} | {ccu}")
            
    except Exception as e:
        print(f"Error al conectar con SteamSpy: {e}")

def obtener_top_100_tag_en_2_semanas(tag):
    # Primero obtenemos el top 100 general de las últimas 2 semanas
    url_top = "https://steamspy.com/api.php?request=top100in2weeks"
    
    try:
        response_top = requests.get(url_top)
        response_top.raise_for_status()
        top_100 = response_top.json()
        
        # Comparamos ignorando mayúsculas/minúsculas
        tag_lower = tag.lower()
        
        print(f"\nTop juegos más jugados ('{tag}' entre sus etiquetas):")
        print(f"{'Ranking Tag':<15} | {'Nombre':<40} | {'AppID':<10} | {'Current Players (CCU)':<25}")
        print("-" * 95)
        
        encontrados = 0
        for i, (appid, info) in enumerate(top_100.items(), 1):
            # Obtener todas las etiquetas de este juego
            tags_juego = obtener_tags_juego(appid, silencioso=True, num_tags=None)
            
            if tag_lower in tags_juego:
                encontrados += 1
                ccu = info.get('ccu', 'N/A')
                nombre = info['name'][:39]
                print(f"{encontrados:<15} | {nombre:<40} | {appid:<10} | {ccu}")
                
        if encontrados == 0:
            print(f"No se encontraron juegos con la etiqueta '{tag}' en el top 100 de las últimas 2 semanas.")
            
    except Exception as e:
        print(f"Error al obtener datos: {e}")

def guardar_top100_con_tags_en_json(nombre_archivo="top100_tags_cache.json", num_tags=5):
    url_top = "https://steamspy.com/api.php?request=top100in2weeks"
    
    tags_msg = "todas sus tags" if num_tags is None else f"sus top {num_tags} tags"
    print(f"Obteniendo top 100 de juegos y {tags_msg}... (Esto puede tardar un poco)")
    
    try:
        response_top = requests.get(url_top)
        response_top.raise_for_status()
        top_100 = response_top.json()
        
        datos_guardar = {}
        
        for appid, info in top_100.items():
            # Obtener tags limitados por num_tags
            tags_juego = obtener_tags_juego(appid, silencioso=True, num_tags=num_tags)
            
            datos_guardar[appid] = {
                'name': info.get('name', 'Unknown'),
                'ccu': info.get('ccu', 0),
                'tags': tags_juego
            }
            
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos_guardar, f, ensure_ascii=False, indent=4)
            
        print(f"Datos correctamente guardados en {nombre_archivo}")
        
    except Exception as e:
        print(f"Error al generar la caché JSON: {e}")

def obtener_top_100_tag_en_2_semanas_desde_json(tag, nombre_archivo="top100_tags_cache.json"):
    if not os.path.exists(nombre_archivo):
        print(f"El archivo {nombre_archivo} no existe. Por favor, genera la caché primero.")
        return
        
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            datos_cache = json.load(f)
            
        tag_lower = tag.lower()
        
        print(f"\nTop juegos más jugados ('{tag}' en sus etiquetas) [DESDE CACHÉ JSON]:")
        print(f"{'Ranking Tag':<15} | {'Nombre':<40} | {'AppID':<10} | {'Current Players (CCU)':<25}")
        print("-" * 95)
        
        encontrados = 0
        
        # Como los iteramos desde el diccionario, queremos mantener el orden de "Ranking General" asumiendo 
        # que el json preserva el orden del top 100 (dict de python > 3.7 preserva el orden de inserción)
        for appid, info in datos_cache.items():
            tags_juego = info.get('tags', info.get('top_5_tags', []))
            
            if tag_lower in tags_juego:
                encontrados += 1
                ccu = info.get('ccu', 'N/A')
                nombre = info['name'][:39]
                print(f"{encontrados:<15} | {nombre:<40} | {appid:<10} | {ccu}")
                
        if encontrados == 0:
            print(f"No se encontraron juegos con la etiqueta '{tag}' en el top 100 en la caché.")
            
    except Exception as e:
        print(f"Error al leer la caché: {e}")

def listar_tags_top_100(nombre_archivo="top100_tags_cache.json"):
    if not os.path.exists(nombre_archivo):
        print(f"El archivo {nombre_archivo} no existe. Por favor, genera la caché primero.")
        return
        
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            datos_cache = json.load(f)
            
        conteo_tags = {}
        
        # Recorrer todos los juegos y contar la frecuencia de cada tag
        for appid, info in datos_cache.items():
            tags_juego = info.get('tags', info.get('top_5_tags', []))
            for tag in tags_juego:
                # Nos aseguramos de guardarla en minúscula uniforme u original para contar
                tag_lower = tag.lower()
                conteo_tags[tag_lower] = conteo_tags.get(tag_lower, 0) + 1
                
        # Ordenar primero por frecuencia (de mayor a menor) y luego alfabéticamente
        tags_ordenadas = sorted(conteo_tags.items(), key=lambda x: (-x[1], x[0]))
        
        print(f"\nTags presentes en el Top 100 actual ({len(tags_ordenadas)} tags diferentes en total):")
        print(f"{'Tag':<30} | {'Frecuencia (Juegos)'}")
        print("-" * 55)
        for tag, freq in tags_ordenadas:
            print(f"{tag.title():<30} | {freq}")
            
    except Exception as e:
        print(f"Error al procesar la caché: {e}")

# Ejecución
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para consultar datos de la API de SteamSpy.")
    
    # ID y Tag son búsquedas diferentes, no se deben proporcionar a la vez.
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--id", type=int, help="El ID del juego para buscar sus tags y recomendaciones.")
    group.add_argument("--tag", type=str, help="La tag por la que buscar en el top 100 (ej. RPG).")
    
    parser.add_argument("--top", action="store_true", help="Obtener el top 100 general de juegos más jugados en 2 semanas.")
    # Argparse con booleanos se maneja mejor usando action
    # Por defecto la caché la usaremos (es más rápido), y se deshabilita con --no-cache
    parser.add_argument("--no-cache", action="store_false", dest="cache", help="Desactiva el uso de la caché JSON para la búsqueda por tag.")
    parser.add_argument("--store_cache", nargs='?', const=5, type=int, metavar='N', help="Actualiza/crea la caché JSON del top 100 guardando N tags por juego (por defecto 5. Usa 0 para guardar todas).")
    
    parser.add_argument("--list_tags", action="store_true", help="Lista todas las tags presentes en los juegos del top 100 y su frecuencia.")

    args = parser.parse_args()

    # Si se pide actualizar la caché, se hace primero
    if args.store_cache is not None:
        num_tags = None if args.store_cache == 0 else args.store_cache
        guardar_top100_con_tags_en_json(num_tags=num_tags)
        
    # Si se pide listar las tags que conforman el top 100 local
    if args.list_tags:
        listar_tags_top_100()

    # Si se pide el top 100 general
    if args.top:
        obtener_top_100_en_2_semanas()

    # Búsqueda por ID (recomendaciones y tags)
    if args.id is not None:
        # Nota: obtener_tags_juego la llamamos pasando silencioso=False implícito
        obtener_tags_juego(args.id)
        obtener_recomendaciones(args.id)
        
    # Búsqueda por Tag (con o sin caché)
    elif args.tag is not None:
        if args.cache:
            obtener_top_100_tag_en_2_semanas_desde_json(args.tag)
        else:
            obtener_top_100_tag_en_2_semanas(args.tag)
    #Cambio
