# TODO LIST
## Endpoints más útiles para testear
Las rutas más comunes que puedes concatenar a BASE_URL:

1. Datos del perfil: ISteamUser/GetPlayerSummaries/v2/
    * Uso: Saber si el usuario está jugando a algo ahora mismo.

2. Lista de amigos: ISteamUser/GetFriendList/v1/
    * Uso: Ver quiénes son sus contactos (solo si su perfil es público).

3. Logros de un usuario: ISteamUserStats/GetPlayerAchievements/v1/
    * Uso: Ver qué retos ha completado el usuario en un appid específico.

## ⚠️ Notas importantes para mejorar:
* Privacidad: Si el perfil del STEAM_ID que se consulta está en "Privado", la API devolverá un JSON vacío o un error, usando o no la key.

* Límites: Steam permite unas 100,000 peticiones por día con la API Key.

* Seguridad: Usar un archivo .env para guardar la KEY.

## Información de Steam
2 fuentes de información para la app web:

* Steam Web API (api.steampowered.com) → datos de usuario (biblioteca, perfil, amigos, etc.)

* Steam Store API (store.steampowered.com/api/...) → metadata del juego (géneros, precio, descripción, etc.)

1) Entrada de usuario: vanity → SteamID64
Si tu web pide “usuario/SteamID”, casi siempre tendrás que resolver vanity URL primero. Hay endpoint específico: ISteamUser/ResolveVanityURL

2) Perfil básico (nombre, avatar, visibilidad)
**GetPlayerSummaries** (útil para mostrar “quién es” el usuario y comprobar privacidad). Referencia general de Web API

3) Biblioteca + horas jugadas (base de recomendaciones)
**IPlayerService/GetOwnedGames** → lista de juegos + playtime_forever (ojo con perfiles privados).

4) “Señales” de gusto: recientemente jugados
**IPlayerService/GetRecentlyPlayedGames**

5) Achievements / stats (si queréis “hardcore score”)
**ISteamUserStats/GetPlayerAchievements** y/o **GetUserStatsForGame**

6) Noticias del juego
**ISteamNews/GetNewsForApp**

7) Catálogo: buscar appid / autocompletar
**ISteamApps/GetAppList/v2** te da el listado masivo (no filtrable)

## Fuentes de información
* Vanity URL: https://wiki.teamfortress.com/wiki/WebAPI/ResolveVanityURL
* Perfil de steam: https://developer.valvesoftware.com/wiki/Steam_Web_API
* Steamworks para información de las llamadas: https://partner.steamgames.com/doc/webapi/iplayerservice

