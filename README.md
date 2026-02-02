# DBapores
Recomendaciones de Steam utilizando la Steam Web API.

DBapores/
├─ README.md                           # Qué hace el proyecto + cómo arrancar (npm i / npm run dev)
├─ .gitignore                          # Ignorar node_modules, .env, logs, etc.
├─ .env.example                        # Plantilla: STEAM_API_KEY=..., PORT=3000, CC=ES, etc.
│
├─ server/                             # Backend mínimo: puente a Steam + lógica de recomendación
│  ├─ package.json                     # Dependencias (express, cors opcional, node-fetch/axios, dotenv)
│  └─ src/
│     ├─ server.js                     # Arranca Express, sirve /public estático, monta rutas /api y escucha PORT
│     ├─ routes.js                     # Define endpoints: /api/profile, /api/recommend/tags, /api/recommend/quiz
│     ├─ config.js                     # Lee process.env (API key, country code, idioma, URLs base) y exporta constantes
│     │
│     ├─ steamApi.js                   # Funciones “HTTP wrapper” a Steam:
│     │                                # - resolver vanity -> steamId (si usáis vanity)
│     │                                # - obtener biblioteca (GetOwnedGames)
│     │                                # - obtener detalles tienda (appdetails) para género/precio/oferta/fecha
│     │
│     ├─ profileService.js             # Crea el “PlayerProfile”:
│     │                                # - normaliza lista de juegos (appid, name, playtime)
│     │                                # - obtiene “tags” (géneros/categorías desde appdetails) por juego
│     │                                # - agrupa tags por frecuencia (Shooter: 4, RPG: 1, ...)
│     │
│     ├─ recommendService.js           # Recomendación:
│     │                                # - por tags: elige top tags, busca candidatos, filtra últimos 2 años,
│     │                                #   ordena priorizando ofertas (discount) y devuelve lista final
│     │                                # - por quiz: aplica filtros (género, precio, año, solo ofertas, etc.)
│     │
│     ├─ cache.js                      # (Opcional pero útil) Caché en memoria/JSON:
│     │                                # - guardar appdetails por appid para no repetir llamadas (demo más rápida)
│     │
│     └─ utils.js                      # Helpers:
│                                      # - contar frecuencias
│                                      # - ordenar top tags
│                                      # - filtrar por fecha (últimos 2 años)
│                                      # - normalizar datos (precio, boolean onSale, etc.)
│
└─ public/                             # Frontend estático (HTML + Bootstrap + JS)
   ├─ index.html                       # Página principal:
   │                                  # - Form SteamID/vanity + botón “Generar perfil”
   │                                  # - Botón “No tengo Steam” -> muestra/abre el quiz
   │                                  # - Contenedores para: tags frecuentes y resultados
   │
   ├─ results.html                     # (Opcional) Si preferís página separada:
   │                                  # - Recibe resultados y los pinta (si no, podéis usar solo index.html)
   │
   ├─ assets/
   │  ├─ css/
   │  │  └─ styles.css                 # Vuestro CSS:
   │  │                                # - ajustes Bootstrap (espaciados, colores, cards)
   │  │                                # - estilos de TagCloud, loaders, etc.
   │  │
   │  ├─ js/
   │  │  ├─ main.js                    # Punto de entrada del front:
   │  │  │                              # - añade event listeners a formularios/botones
   │  │  │                              # - decide si ejecutar steamFlow o quizFlow
   │  │  │
   │  │  ├─ apiClient.js               # Cliente fetch al backend:
   │  │  │                              # - postProfile(steamIdOrVanity)
   │  │  │                              # - recommendByTags(tagsTop)
   │  │  │                              # - recommendByQuiz(filters)
   │  │  │
   │  │  ├─ state.js                   # “Modelo” (estado en memoria):
   │  │  │                              # - profile actual (games, tagsFreq)
   │  │  │                              # - filtros quiz seleccionados
   │  │  │                              # - resultados actuales
   │  │  │
   │  │  ├─ steamFlow.js               # Flujo Steam:
   │  │  │                              # - leer steamId/vanity del form
   │  │  │                              # - llamar /api/profile
   │  │  │                              # - elegir top tags y llamar /api/recommend/tags
   │  │  │                              # - guardar en state y pedir render
   │  │  │
   │  │  ├─ quizFlow.js                # Flujo Quiz:
   │  │  │                              # - leer checkboxes (géneros, precio, año, oferta)
   │  │  │                              # - llamar /api/recommend/quiz
   │  │  │                              # - guardar en state y pedir render
   │  │  │
   │  │  └─ render.js                  # Render UI:
   │  │                                 # - pintar tags con frecuencia (badges)
   │  │                                 # - pintar lista de juegos recomendados (cards)
   │  │                                 # - mostrar loaders/errores/vacíos
   │  │
   │  └─ img/                          # Logos/placeholder imágenes
   │     ├─ logo.png
   │     └─ placeholder-game.png
   │
   └─ components/                      # (Opcional) “partials” HTML si queréis reutilizar trozos
      ├─ navbar.html                   # Barra superior común
      └─ footer.html                   # Pie común


112E7CAE5268A96388B6FB4E3FDCFFB9