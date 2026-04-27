import requests
import time
import csv

API_KEY = "428BA0E899DAECC321FF9CBBCE3540A6"
STEAM_ID = "76561199116601828"

print("Obteniendo tu top 10 de juegos más jugados...")

# 1. Obtener la biblioteca completa
url_games = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={API_KEY}&steamid={STEAM_ID}&include_appinfo=true&format=json"
res_games = requests.get(url_games).json()
juegos = res_games.get('response', {}).get('games', [])

# 2. Ordenar por tiempo de juego y coger los 10 primeros
juegos_top = sorted(juegos, key=lambda x: x.get('playtime_forever', 0), reverse=True)[:10]

# 3. Crear el archivo CSV
with open('mis_logros_top10.csv', mode='w', newline='', encoding='utf-8-sig') as archivo_csv:
    writer = csv.writer(archivo_csv, delimiter=';')
    writer.writerow(['Juego', 'Horas', 'Logro', 'Estado', 'Descripción'])

    for juego in juegos_top:
        app_id = juego['appid']
        nombre_juego = juego['name']
        horas = round(juego.get('playtime_forever', 0) / 60, 1)
        
        print(f"Procesando: {nombre_juego} ({horas}h)...", end=" ")
        
        # Petición de logros del jugador
        url_user = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?key={API_KEY}&steamid={STEAM_ID}&appid={app_id}&l=spanish"
        res_user = requests.get(url_user)
        
        # Si la respuesta es correcta (200 OK) extraemos los datos
        if res_user.status_code == 200:
            data = res_user.json()
            logros = data.get("playerstats", {}).get("achievements", [])
            
            if logros:
                obtenidos = 0
                for logro in logros:
                    # Usamos el nombre real si viene, si no, el código interno
                    nombre_logro = logro.get('name', logro['apiname'])
                    desc = logro.get('description', 'Sin descripción')
                    estado = "Obtenido" if logro['achieved'] == 1 else "Pendiente"
                    
                    if logro['achieved'] == 1: obtenidos += 1
                    
                    writer.writerow([nombre_juego, horas, nombre_logro, estado, desc])
                
                print(f"✅ {obtenidos}/{len(logros)} logros exportados.")
            else:
                print("⚠️ El juego no tiene lista de logros.")
        else:
            # Aquí caerán los Playtests, Betas o juegos sin soporte
            print("❌ Sin logros compatibles o estadisticas privadas.")
        
        # Pequeña pausa para no saturar la API
        time.sleep(0.5)

print("\n¡Proceso completado! Se ha generado el archivo 'mis_logros_top10.csv'.")