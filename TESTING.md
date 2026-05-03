# Estrategia de pruebas (DBapores)

## Resumen
Este proyecto (Flask) se prueba con una estrategia **por capas**:

- **Pruebas unitarias (tests/unit)**: validan lógica pura y reglas de negocio aisladas (sin red y sin depender de ficheros reales del repo).
- **Pruebas de integración (tests/integration)**: validan la capa HTTP (controllers) usando `Flask.test_client`, simulando dependencias con *fakes*/*monkeypatch*.

Principios clave:
- **Offline first**: no se permite red en tests. En `tests/conftest.py` se bloquean requests HTTP y se usan *mocks/fakes*.
- **Sin datos reales**: cuando se necesita filesystem, se usa `tmp_path` (CSV/JSON temporales).
- **Mínimos cambios en producción**: solo se ajusta producción si es imprescindible para testear (y se justifica).

## Caja negra vs caja blanca
- **Caja negra**: se valida el comportamiento observable (inputs → outputs / códigos HTTP / JSON), sin depender de detalles internos.
  - Ej.: endpoints `/api/*` con `test_client`, validación de status codes y payload.
- **Caja blanca**: se cubren ramas internas y casos límite conocidos del código.
  - Ej.: normalización de nombres/tags, límites (top 30%), desempates de ordenación, manejo de JSON inválido.

En general, se prioriza caja negra en controllers y caja blanca en lógica de dominio.

## Comandos
Instalación de dependencias de test:

```bash
python -m pip install -r requirements-dev.txt
```

Ejecutar todos los tests:
```bash
pytest
```

Ejecutar con coverage:
```bash
pytest --cov=app
```

Ejecutar solo unitarios / integración:
```bash
pytest tests/unit
pytest tests/integration
```

Ejecutar un fichero concreto:
```bash
pytest tests/unit/test_game_catalog_service.py
pytest tests/integration/test_api_controller.py
```

## Casos de prueba automatizados

> Convención de IDs: `UT-` (unit), `IT-` (integration)

|        ID | Módulo                                           | Tipo        | Técnica     | Entrada/caso                                | Resultado esperado                                       |
| --------: | ------------------------------------------------ | ----------- | ----------- | ------------------------------------------- | -------------------------------------------------------- |
| UT-GCS-01 | `app/services/game_catalog_service.py`           | Unit        | Caja blanca | `normalize_search_name(None)`               | `""`                                                     |
| UT-GCS-02 | `app/services/game_catalog_service.py`           | Unit        | Caja blanca | espacios extra / mayúsculas                 | normaliza a minúsculas y colapsa espacios                |
| UT-GCS-03 | `app/services/game_catalog_service.py`           | Unit        | Caja blanca | `"Rainbow Six® Siege™ ©"`                   | `"rainbow six siege"`                                    |
| UT-GCS-04 | `app/services/game_catalog_service.py`           | Unit        | Caja negra  | `get_appid_by_name` con CSV temporal        | devuelve appid correcto                                  |
| UT-GCS-05 | `app/services/game_catalog_service.py`           | Unit        | Caja negra  | `search_games` con `limit=2`                | devuelve como máximo 2 resultados                        |
| UT-REC-01 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | owned contiene un appid candidato           | no recomienda juegos poseídos                            |
| UT-REC-02 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | tags múltiples para mismo juego             | acumula `tagsCoincidentes` (lista ordenada)              |
| UT-REC-03 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | tag sin fichero/datos                       | incluye tag en `missing_tag_files`                       |
| UT-REC-04 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | sponsored + `relevancia_max>=0.6`           | boost (+100) en `coincidencias`                          |
| UT-REC-05 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | sponsored + `relevancia_max<0.6`            | no aplica boost                                          |
|  UT-TR-01 | `app/repositories/tag_repository.py`             | Unit        | Caja negra  | fichero de tag no existe                    | devuelve `[]`                                            |
|  UT-TR-02 | `app/repositories/tag_repository.py`             | Unit        | Caja blanca | tag con espacios (`"Action RPG"`)           | busca `action_rpg.json` y carga                          |
|  UT-TR-03 | `app/repositories/tag_repository.py`             | Unit        | Caja blanca | JSON inválido                               | devuelve `[]` (robusto)                                  |
| UT-RGS-01 | `app/strategies/relevant_games_strategy.py`      | Unit        | Caja blanca | lista vacía                                 | `[]`                                                     |
| UT-RGS-02 | `app/strategies/relevant_games_strategy.py`      | Unit        | Caja blanca | >= 30 juegos                                | devuelve `ceil(30%)` top por playtime                    |
| UT-RSS-01 | `app/strategies/recommendation_sort_strategy.py` | Unit        | Caja blanca | candidatos con empates                      | orden por coincidencias, relevancias, positivos y nombre |
| UT-SLS-01 | `app/services/steam_library_service.py`          | Unit        | Caja blanca | logros vacíos                               | `None`                                                   |
| UT-SLS-02 | `app/services/steam_library_service.py`          | Unit        | Caja blanca | logros + global %                           | calcula porcentaje, rarest (máx 3) e iconos              |
| UT-SLS-03 | `app/services/steam_library_service.py`          | Unit        | Caja blanca | excepciones en cliente                      | devuelve `None`                                          |
| IT-API-01 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/recommend` steamId inválido           | 400 + JSON error                                         |
| IT-API-02 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/recommend` API key sin configurar     | 500                                                      |
| IT-API-03 | `app/controllers/api_controller.py`              | Integración | Caja blanca | parche `build_facade` y `/api/recommend` OK | 200 + JSON esperado                                      |
| IT-API-04 | `app/controllers/api_controller.py`              | Integración | Caja blanca | facade lanza `ValueError`                   | 404 + JSON error                                         |
| IT-API-05 | `app/controllers/api_controller.py`              | Integración | Caja blanca | facade lanza `Exception`                    | 500 + mensaje genérico                                   |
| IT-API-06 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/search_games` query < 2               | `[]`                                                     |
| IT-API-07 | `app/controllers/api_controller.py`              | Integración | Caja blanca | `/api/search_games` con facade mock         | lista esperada                                           |
| IT-API-08 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/wrapped/<steam_id>` inválido          | 400                                                      |

## Pruebas manuales recomendadas (demo)

| Área          | Prueba manual     | Pasos                                            | Resultado esperado                                         |
| ------------- | ----------------- | ------------------------------------------------ | ---------------------------------------------------------- |
| Home          | Carga de UI       | abrir `/`                                        | renderiza `index.html`                                     |
| Recomendador  | Flujo básico      | abrir `/recomendador`, introducir SteamID (demo) | muestra recomendaciones o mensaje de error manejado        |
| API recommend | Validación inputs | llamar `/api/recommend?steamId=...`              | 400 en inválidos; 200 en válidos (con API key configurada) |
| API search    | Autocompletado    | llamar `/api/search_games?q=al`                  | lista de sugerencias                                       |
| Wrapped       | Pantalla wrapped  | abrir `/wrapped` y probar con un SteamID         | HTML/JSON según `Accept`                                   |

## Coverage actual
Ejecutado con:
```bash
pytest --cov=app --cov-report=term
```

### Resumen (última ejecución):

El objetivo no ha sido alcanzar el 100% de cobertura, sino cubrir la lógica propia del proyecto y evitar dependencias externas mediante mocks/fakes.

**53 tests passed. TOTAL coverage: 51%**


Módulos con mejor cobertura:
- `app/services/steam_library_service.py`: 100%
- `app/repositories/tag_repository.py`: 96%
- `app/services/recommendation_service.py`: 96%
- `app/services/game_catalog_service.py`: 93%

Módulos con menor cobertura (pendiente de mejorar):
- `app/clients/steam_api_client.py`, `app/clients/steamspy_client.py` (clientes HTTP)
- `app/services/recommendation_facade.py`, `app/services/tag_profile_service.py`
- `app/utils/disk_cache.py`

## Limitaciones
- **Steam API** y **SteamSpy** no se prueban con llamadas reales en tests automatizados.
- Se usan **mocks/fakes/monkeypatch** para simular respuestas de clientes externos.
- Los tests deben poder ejecutarse **sin conexión** y sin depender de ficheros reales en `data/` (salvo que se estén probando explícitamente como integración con `tmp_path`).
