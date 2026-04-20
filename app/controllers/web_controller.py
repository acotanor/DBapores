from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def home():
    return render_template("index.html")


@web_bp.get("/opcion1")
def opcion1():
    return render_template("opcion1.html")

@web_bp.get("/opcion2")
def opcion2():
    return render_template("opcion2.html")


@web_bp.get("/opcion3")
def opcion3():
    return render_template("wrapped_input.html")