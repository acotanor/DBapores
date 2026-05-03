# Steam Recommender con Flask

## Instalación

```bash
python -m pip install -r requirements-dev.txt
pytest tests/unit/test_*.py
pytest test/integration/test_api_controller.py
# o:
pytest --cov=app