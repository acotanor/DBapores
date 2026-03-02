import requests
import json
import os
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

def obtener_tags_juego(appid, silencioso=False):
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
            
            # Devolvemos solo la lista de nombres de tags (los 5 primeros)
            return [t[0].lower() for t in tags_sorted[:5]]
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
    top_5_tags = obtener_tags_juego(appid, silencioso=True)
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
        
        print(f"\nTop juegos más jugados ('{tag}' en el top 5 de etiquetas):")
        print(f"{'Ranking Tag':<15} | {'Nombre':<40} | {'AppID':<10} | {'Current Players (CCU)':<25}")
        print("-" * 95)
        
        encontrados = 0
        for i, (appid, info) in enumerate(top_100.items(), 1):
            # Obtener el top 5 de este juego
            top_5_juego = obtener_tags_juego(appid, silencioso=True)
            
            if tag_lower in top_5_juego:
                encontrados += 1
                ccu = info.get('ccu', 'N/A')
                nombre = info['name'][:39]
                print(f"{encontrados:<15} | {nombre:<40} | {appid:<10} | {ccu}")
                
        if encontrados == 0:
            print(f"No se encontraron juegos con la etiqueta '{tag}' en el top 100 de las últimas 2 semanas.")
            
    except Exception as e:
        print(f"Error al obtener datos: {e}")

def guardar_top100_con_tags_en_json(nombre_archivo="top100_tags_cache.json"):
    url_top = "https://steamspy.com/api.php?request=top100in2weeks"
    
    print("Obteniendo top 100 de juegos y sus top 5 tags... (Esto puede tardar un poco)")
    
    try:
        response_top = requests.get(url_top)
        response_top.raise_for_status()
        top_100 = response_top.json()
        
        datos_guardar = {}
        
        for appid, info in top_100.items():
            # Obtener el top 5 para este juego
            top_5_juego = obtener_tags_juego(appid, silencioso=True)
            
            datos_guardar[appid] = {
                'name': info.get('name', 'Unknown'),
                'ccu': info.get('ccu', 0),
                'top_5_tags': top_5_juego
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
        
        print(f"\nTop juegos más jugados ('{tag}' en el top 5) [DESDE CACHÉ JSON]:")
        print(f"{'Ranking Tag':<15} | {'Nombre':<40} | {'AppID':<10} | {'Current Players (CCU)':<25}")
        print("-" * 95)
        
        encontrados = 0
        
        # Como los iteramos desde el diccionario, queremos mantener el orden de "Ranking General" asumiendo 
        # que el json preserva el orden del top 100 (dict de python > 3.7 preserva el orden de inserción)
        for appid, info in datos_cache.items():
            top_5_juego = info.get('top_5_tags', [])
            
            if tag_lower in top_5_juego:
                encontrados += 1
                ccu = info.get('ccu', 'N/A')
                nombre = info['name'][:39]
                print(f"{encontrados:<15} | {nombre:<40} | {appid:<10} | {ccu}")
                
        if encontrados == 0:
            print(f"No se encontraron juegos con la etiqueta '{tag}' en el top 100 en la caché.")
            
    except Exception as e:
        print(f"Error al leer la caché: {e}")

# Ejecución
if __name__ == "__main__":
    # 1. Listar shooters generales
    # obtener_shooters_por_genero()
    
    # 2. Obtener tags de un juego específico
    id_apex = 1046930
    # obtener_tags_juego(id_apex)
    
    # 3. Recomendaciones basadas en tags
    # obtener_recomendaciones(id_apex)

    # 4. Top 100 jugados en 2 semanas
    # obtener_top_100_en_2_semanas()
    
    # 5. Top jugados en 2 semanas por Tag
    # obtener_top_100_tag_en_2_semanas("RPG")
    
    # 6. Generar Caché JSON del top100 y sus tags (Descomentar para crearla/actualizarla la primera vez)
    # guardar_top100_con_tags_en_json()
    
    # 7. Leer top por tag desde la caché JSON
    obtener_top_100_tag_en_2_semanas_desde_json("RPG")
