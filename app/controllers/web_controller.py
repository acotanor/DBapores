from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def home():
    return render_template("index.html")


@web_bp.get("/opcion1")
def opcion1():
    return render_template("opcion1.html")