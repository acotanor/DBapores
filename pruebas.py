import requests

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

def obtener_tags_juego(appid):
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        datos = response.json()
        
        if 'tags' in datos and datos['tags']:
            print(f"\nTags para {datos['name']} (ID: {appid}):")
            # Los tags vienen como un diccionario {nombre_tag: votos}
            tags_sorted = sorted(datos['tags'].items(), key=lambda x: x[1], reverse=True)
            for tag, votos in tags_sorted[:20]: # Mostramos los 20 principales
                print(f"- {tag} ({votos} votos)")
        else:
            print(f"No se encontraron tags para el AppID {appid}.")
            
    except Exception as e:
        print(f"Error al obtener tags: {e}")

def obtener_recomendaciones(appid):
    # 1. Obtener los 5 tags más populares del juego base
    url_base = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    try:
        resp = requests.get(url_base)
        datos_juego = resp.json()
        nombre_original = datos_juego['name']
        tags_dict = datos_juego.get('tags', {})
        
        # Ordenar tags por votos y pillar los 5 primeros
        top_5_tags = sorted(tags_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        print(top_5_tags)
        tags_nombres = [t[0] for t in top_5_tags]
        print(tags_nombres)
        if not tags_nombres:
            print("No se encontraron tags para este juego.")
            return

        print(f"\nBuscando recomendaciones para '{nombre_original}' basadas en: {', '.join(tags_nombres)}")
        
        # 2. Buscar juegos para cada tag y contar coincidencias
        coincidencias = {} # {appid: {'count': N, 'name': 'Name'}}
        
        for tag in tags_nombres:
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

# Ejecución
if __name__ == "__main__":
    # 1. Listar shooters generales
    obtener_shooters_por_genero()
    
    # 2. Obtener tags de un juego específico
    id_apex = 1046930
    obtener_tags_juego(id_apex)
    
    # 3. Recomendaciones basadas en tags
    obtener_recomendaciones(id_apex)

    # 4. Top 100 jugados en 2 semanas
    obtener_top_100_en_2_semanas()
