# DBapores - Instrucciones para Copilot

Este proyecto es una aplicación Flask de recomendaciones de Steam.

## Reglas generales

- Usa Python con pytest para las pruebas.
- No hagas llamadas reales a Steam API ni a SteamSpy en los tests.
- No uses API keys reales.
- Los tests deben poder ejecutarse offline.
- Usa mocks, fakes, fixtures, monkeypatch y tmp_path.
- No modifiques lógica de producción salvo que sea estrictamente necesario.
- Si hay que modificar código de producción para hacerlo testeable, haz cambios mínimos y explícalos.
- No añadas secretos al repositorio.
- No copies claves de .env en tests ni documentación.
- Prioriza código claro y fácil de explicar en una presentación académica.

## Estructura de tests

Usa esta estructura:

tests/
├── conftest.py
├── unit/
└── integration/

## Criterios de calidad

- Nombres de tests descriptivos.
- Un test debe comprobar una idea concreta.
- Evitar dependencias de red.
- Evitar datos externos salvo archivos temporales creados con tmp_path.
- Mantener separados tests unitarios e integración.
- Preferir fixtures reutilizables en conftest.py.
- Al añadir tests, indica qué casos son caja negra y cuáles caja blanca.

## Comandos esperados

pytest
pytest --cov=app