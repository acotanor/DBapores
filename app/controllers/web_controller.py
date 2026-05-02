from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def home():
    return render_template("index.html")


@web_bp.get("/recomendador")
def recomendador():
    return render_template("recomendador.html")

@web_bp.get("/explorador")
def explorador():
    return render_template("explorador.html")


@web_bp.get("/wrapped")
def wrapped():
    return render_template("wrapped_input.html")