# TESTING

Tabla de casos de prueba para las rutas web y la API.

| ID | Funcionalidad | Tipo de prueba | Entrada | Resultado esperado | Automatizado/Manual |
| --- | --- | --- | --- | --- | --- |
| TC-001 | Página de inicio | UI/Smoke | GET / | Responde 200 y renderiza `index.html`. | Manual |
| TC-002 | Página de recomendador | UI/Smoke | GET /recomendador | Responde 200 y renderiza `recomendador.html`. | Manual |
| TC-003 | Página de explorador | UI/Smoke | GET /explorador | Responde 200 y renderiza `explorador.html`. | Manual |
| TC-004 | Página de Wrapped (formulario) | UI/Smoke | GET /wrapped | Responde 200 y renderiza `wrapped_input.html`. | Manual |
| TC-005 | Validación de Steam ID en recomendaciones | API/Validación | GET /api/recommend?steamId=123 | Responde 400 con error de Steam ID inválido. | Manual |
| TC-006 | Recomendaciones con Steam ID válido | API/Integración | GET /api/recommend?steamId=<steamId válido> | Responde 200 con `steamId`, `topTags`, `recommendations`, `featured`, `ownedGames` y `stats`. | Manual |
| TC-007 | Recomendaciones sin API Key configurada | API/Negativa | GET /api/recommend?steamId=<steamId válido> con `STEAM_API_KEY` por defecto | Responde 500 con error de configuración de API Key. | Manual |
| TC-008 | Wrapped HTML | API/Integración | GET /api/wrapped/<steamId válido> con `Accept: text/html` | Responde 200 con HTML generado desde `wrapped.html`. | Manual |
| TC-009 | Wrapped filtrado sin parámetros | API/Validación | GET /api/wrapped_filtered | Responde 400 con error por falta de `steamId` o `tag`. | Manual |
| TC-010 | Recomendación por juego con appId vacío | API/Validación | GET /api/recommend_by_game?appId= | Responde 400 con error de entrada vacía. | Manual |
| TC-011 | Búsqueda con query corta | API/Funcional | GET /api/search_games?q=a | Responde 200 con lista vacía. | Manual |
| TC-012 | Búsqueda con query válida | API/Funcional | GET /api/search_games?q=portal | Responde 200 con lista de coincidencias. | Manual |
