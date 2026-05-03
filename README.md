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

## Resultado actual

- **63 tests automatizados** (unitarios + integración)
- **57% de cobertura total** (`pytest-cov`)
- Ejecución **offline** (sin llamadas reales a Steam API / SteamSpy)
- Herramientas y técnicas usadas: `pytest`, `pytest-cov`, `tmp_path`, *mocks/fakes* y `monkeypatch`

## Casos de prueba automatizados

> Convención de IDs: `UT-` (unit), `IT-` (integration)

|        ID | Módulo                                           | Tipo        | Técnica     | Entrada/caso                                              | Resultado esperado                                         |
| --------: | ------------------------------------------------ | ----------- | ----------- | --------------------------------------------------------- | ---------------------------------------------------------- |
| UT-GCS-01 | `app/services/game_catalog_service.py`           | Unit        | Caja blanca | `normalize_search_name(None)`                             | `""`                                                       |
| UT-GCS-02 | `app/services/game_catalog_service.py`           | Unit        | Caja blanca | espacios extra / mayúsculas                               | normaliza a minúsculas y colapsa espacios                  |
| UT-GCS-03 | `app/services/game_catalog_service.py`           | Unit        | Caja blanca | `"Rainbow Six® Siege™ ©"`                                 | `"rainbow six siege"`                                      |
| UT-GCS-04 | `app/services/game_catalog_service.py`           | Unit        | Caja negra  | `get_appid_by_name` con CSV temporal                      | devuelve appid correcto                                    |
| UT-GCS-05 | `app/services/game_catalog_service.py`           | Unit        | Caja negra  | `search_games` con `limit=2`                              | devuelve como máximo 2 resultados                          |
|  UT-DC-01 | `app/utils/disk_cache.py`                        | Unit        | Caja negra  | `get()` con clave inexistente                             | `None`                                                     |
|  UT-DC-02 | `app/utils/disk_cache.py`                        | Unit        | Caja negra  | `set()` + `get()`                                         | roundtrip del valor                                        |
|  UT-DC-03 | `app/utils/disk_cache.py`                        | Unit        | Caja blanca | clave con `/` o espacios                                  | se sanitiza a fichero seguro (`a_b_c.json`)                |
|  UT-DC-04 | `app/utils/disk_cache.py`                        | Unit        | Caja blanca | fichero de caché con JSON inválido                        | `get()` devuelve `None`                                    |
|  UT-DC-05 | `app/utils/disk_cache.py`                        | Unit        | Caja negra  | `set()` sobre una clave existente                         | sobrescribe el valor                                       |
| UT-REC-01 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | owned contiene un appid candidato                         | no recomienda juegos poseídos                              |
| UT-REC-02 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | tags múltiples para mismo juego                           | acumula `tagsCoincidentes` (lista ordenada)                |
| UT-REC-03 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | tag sin fichero/datos                                     | incluye tag en `missing_tag_files`                         |
| UT-REC-04 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | sponsored + `relevancia_max>=0.6`                         | boost (+100) en `coincidencias`                            |
| UT-REC-05 | `app/services/recommendation_service.py`         | Unit        | Caja blanca | sponsored + `relevancia_max<0.6`                          | no aplica boost                                            |
| UT-TPS-01 | `app/services/tag_profile_service.py`            | Unit        | Caja negra  | sin juegos relevantes                                     | `top_tags=[]`, sin llamadas al cliente                     |
| UT-TPS-02 | `app/services/tag_profile_service.py`            | Unit        | Caja blanca | conteo de tags + desempate alfabético                     | top tags ordenados por frecuencia y luego por nombre       |
| UT-TPS-03 | `app/services/tag_profile_service.py`            | Unit        | Caja blanca | `steamspy_tags_per_game=2`                                | se pasa `num_tags=2` al cliente fake                       |
| UT-TPS-04 | `app/services/tag_profile_service.py`            | Unit        | Caja blanca | `steamspy_client.get_top_tags` lanza excepción            | se ignora y se cuenta como `[]`                            |
| UT-TPS-05 | `app/services/tag_profile_service.py`            | Unit        | Caja negra  | todos los juegos devuelven tags vacíos                    | `top_tags=[]`                                              |
| UT-TXT-01 | `app/utils/text_utils.py`                        | Unit        | Caja blanca | normalizar tag con espacios (`"Action RPG"`) *(indirect)* | produce `action_rpg` (vía `TagRepository`)                 |
| UT-TGA-01 | `app/adapters/tag_game_adapter.py`               | Unit        | Caja blanca | adaptar `appid/name/positive/relevancia` *(indirect)*     | coerción de tipos + campos esperados (vía `TagRepository`) |
|  UT-TR-01 | `app/repositories/tag_repository.py`             | Unit        | Caja negra  | fichero de tag no existe                                  | devuelve `[]`                                              |
|  UT-TR-02 | `app/repositories/tag_repository.py`             | Unit        | Caja blanca | tag con espacios (`"Action RPG"`)                         | busca `action_rpg.json` y carga                            |
|  UT-TR-03 | `app/repositories/tag_repository.py`             | Unit        | Caja blanca | JSON inválido                                             | devuelve `[]` (robusto)                                    |
| UT-RGS-01 | `app/strategies/relevant_games_strategy.py`      | Unit        | Caja blanca | lista vacía                                               | `[]`                                                       |
| UT-RGS-02 | `app/strategies/relevant_games_strategy.py`      | Unit        | Caja blanca | >= 30 juegos                                              | devuelve `ceil(30%)` top por playtime                      |
| UT-RSS-01 | `app/strategies/recommendation_sort_strategy.py` | Unit        | Caja blanca | candidatos con empates                                    | orden por coincidencias, relevancias, positivos y nombre   |
| UT-SLS-01 | `app/services/steam_library_service.py`          | Unit        | Caja blanca | logros vacíos                                             | `None`                                                     |
| UT-SLS-02 | `app/services/steam_library_service.py`          | Unit        | Caja blanca | logros + global %                                         | calcula porcentaje, rarest (máx 3) e iconos                |
| UT-SLS-03 | `app/services/steam_library_service.py`          | Unit        | Caja blanca | excepciones en cliente                                    | devuelve `None`                                            |
| IT-API-01 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/recommend` steamId inválido                         | 400 + JSON error                                           |
| IT-API-02 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/recommend` API key sin configurar                   | 500                                                        |
| IT-API-03 | `app/controllers/api_controller.py`              | Integración | Caja blanca | parche `build_facade` y `/api/recommend` OK               | 200 + JSON esperado                                        |
| IT-API-04 | `app/controllers/api_controller.py`              | Integración | Caja blanca | facade lanza `ValueError`                                 | 404 + JSON error                                           |
| IT-API-05 | `app/controllers/api_controller.py`              | Integración | Caja blanca | facade lanza `Exception`                                  | 500 + mensaje genérico                                     |
| IT-API-06 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/search_games` query < 2                             | `[]`                                                       |
| IT-API-07 | `app/controllers/api_controller.py`              | Integración | Caja blanca | `/api/search_games` con facade mock                       | lista esperada                                             |
| IT-API-08 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/wrapped/<steam_id>` inválido                        | 400                                                        |
| IT-API-09 | `app/controllers/api_controller.py`              | Integración | Caja blanca | `/api/recommend_by_game` con facade mock                  | 200 + JSON esperado                                        |
| IT-API-10 | `app/controllers/api_controller.py`              | Integración | Caja blanca | `/api/recommend_by_game` lanza `ValueError`               | 404 + JSON error                                           |
| IT-API-11 | `app/controllers/api_controller.py`              | Integración | Caja negra  | `/api/recommend_by_game` sin `appId`                      | 400 + JSON error                                           |

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

### Resumen (última ejecución)

- **63 tests passed**
- **TOTAL: 57%**

Módulos con mejor cobertura (última ejecución):
- `app/services/steam_library_service.py`: 100%
- `app/services/tag_profile_service.py`: 100%
- `app/utils/text_utils.py`: 100%
- `app/adapters/tag_game_adapter.py`: 100%
- `app/repositories/tag_repository.py`: 96%
- `app/services/recommendation_service.py`: 96%
- `app/services/game_catalog_service.py`: 93%
- `app/strategies/relevant_games_strategy.py`: 93%
- `app/utils/disk_cache.py`: 91%

Módulos con menor cobertura (pendiente de mejorar):
- `app/clients/steam_api_client.py`, `app/clients/steamspy_client.py` (clientes HTTP)
- `app/services/recommendation_facade.py` (orquesta lógica y depende de capas externas)
- `app/controllers/api_controller.py` (parte cubierta vía integración; queda lógica por cubrir)

## Interpretación del coverage

- No se busca **100% de cobertura**: la meta es tener confianza en la lógica propia del proyecto.
- La prioridad ha sido cubrir **servicios, repositorios, estrategias y utilidades** (lógica “nuestra”).
- Los módulos con menor cobertura son principalmente **clientes HTTP** o capas que dependen de **APIs externas**.
- Es preferible **mockear** Steam API y SteamSpy para que los tests sean **rápidos, deterministas y offline**.

## Limitaciones
- **Steam API** y **SteamSpy** no se prueban con llamadas reales en tests automatizados.
- Se usan **mocks/fakes/monkeypatch** para simular respuestas de clientes externos.
- Los tests deben poder ejecutarse **sin conexión** y sin depender de ficheros reales en `data/` (salvo que se estén probando explícitamente como integración con `tmp_path`).

## Ejecución del proyecto

```bash
python -m pip install -r requirements.txt
python run.py