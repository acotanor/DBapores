from flask import Flask
from .config import Config
from .controllers.web_controller import web_bp
from .controllers.api_controller import api_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app