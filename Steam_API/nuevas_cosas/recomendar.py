import json
import os
import re
import unicodedata
from math import ceil
from collections import Counter

import requests

from saca_biblioteca import crear_lista_juegos_desde_steam, API_KEY

STEAMSPY_URL = "https://steamspy.com/api.php"
CARPETA_TAGS = os.path.join(os.path.dirname(__file__), "tags")


def obtener_tags_juego(appid, silencioso=False, num_tags=5):
    """
    Obtiene las tags más importantes de un juego desde SteamSpy.
    - appid: ID del juego en Steam
    - silencioso: si es False, imprime las tags por consola
    - num_tags: número de tags a devolver; si es None, devuelve todas
    """
    url = f"{STEAMSPY_URL}?request=appdetails&appid={appid}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        datos = response.json()

        if "tags" in datos and isinstance(datos["tags"], dict) and datos["tags"]:
            tags_sorted = sorted(datos["tags"].items(), key=lambda x: x[1], reverse=True)

            if not silencioso:
                print(f"\nTags para {datos.get('name', 'Juego desconocido')} (ID: {appid}):")
                for tag, votos in tags_sorted[:20]:
                    print(f"- {tag} ({votos} votos)")

            if num_tags is not None:
                return [tag[0].lower() for tag in tags_sorted[:num_tags]]
            return [tag[0].lower() for tag in tags_sorted]

        if not silencioso:
            print(f"No se encontraron tags para el AppID {appid}.")
        return []

    except requests.exceptions.RequestException as e:
        if not silencioso:
            print(f"Error al obtener tags para el AppID {appid}: {e}")
        return []


def obtener_juegos_relevantes(lista_juegos):
    """
    Selecciona los juegos sobre los que se van a sacar tags:
    - si la lista tiene menos de 30 juegos, devuelve todos
    - si no, devuelve el 30% más jugado
    """
    total = lista_juegos.total_juegos()

    if total == 0:
        return []

    lista_juegos.ordenar_por_tiempo_jugado()

    if total < 30:
        return lista_juegos.juegos

    cantidad = ceil(total * 0.30)
    return lista_juegos.juegos[:cantidad]


def recolectar_tags_frecuentes(lista_juegos, num_tags_por_juego=5):
    """
    Recolecta las tags principales de los juegos relevantes y devuelve
    un contador con sus frecuencias.
    """
    juegos_relevantes = obtener_juegos_relevantes(lista_juegos)
    contador_tags = Counter()

    for juego in juegos_relevantes:
        tags = obtener_tags_juego(juego.appid, silencioso=True, num_tags=num_tags_por_juego)
        contador_tags.update(tags)

    return contador_tags


def obtener_top_tags_usuario(lista_juegos, num_tags_por_juego=5, top_n=5):
    """
    Devuelve una lista con las top_n tags más frecuentes del usuario.
    """
    contador_tags = recolectar_tags_frecuentes(
        lista_juegos,
        num_tags_por_juego=num_tags_por_juego
    )
    return [tag for tag, _ in contador_tags.most_common(top_n)]


def normalizar_tag_a_nombre_archivo(tag):
    """
    Convierte una tag tipo:
      'story rich' -> 'story_rich'
      'co-op' -> 'co_op'
      'souls-like' -> 'souls_like'
    para poder buscar su JSON correspondiente.
    """
    tag = tag.strip().lower()
    tag = unicodedata.normalize("NFKD", tag).encode("ascii", "ignore").decode("utf-8")
    tag = tag.replace("&", "and")
    tag = re.sub(r"[ /-]+", "_", tag)
    tag = re.sub(r"[^a-z0-9_]", "", tag)
    tag = re.sub(r"_+", "_", tag).strip("_")
    return tag


def cargar_juegos_de_tag(tag, carpeta_tags=CARPETA_TAGS):
    """
    Carga el JSON asociado a una tag y devuelve la lista de juegos.
    """
    nombre_archivo = normalizar_tag_a_nombre_archivo(tag) + ".json"
    ruta_archivo = os.path.join(carpeta_tags, nombre_archivo)

    if not os.path.exists(ruta_archivo):
        return []

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
            if isinstance(datos, list):
                return datos
            return []
    except (OSError, json.JSONDecodeError):
        return []


def recomendar_juegos_desde_json(
    lista_juegos,
    carpeta_tags=CARPETA_TAGS,
    num_tags_por_juego=5,
    top_tags_usuario=5,
    top_recomendaciones=5
):
    """
    A partir de las top tags del usuario:
    - busca los JSON de esas tags,
    - une juegos repetidos entre varios JSON,
    - puntúa por número de tags en común,
    - desempata por relevancia_total, relevancia_max y positive,
    - excluye juegos que el usuario ya posee.
    """
    tags_usuario = obtener_top_tags_usuario(
        lista_juegos,
        num_tags_por_juego=num_tags_por_juego,
        top_n=top_tags_usuario
    )

    if not tags_usuario:
        return [], [], []

    appids_usuario = {str(juego.appid) for juego in lista_juegos.juegos}
    candidatos = {}
    tags_sin_json = []

    for tag in tags_usuario:
        juegos_de_esa_tag = cargar_juegos_de_tag(tag, carpeta_tags=carpeta_tags)

        if not juegos_de_esa_tag:
            tags_sin_json.append(tag)
            continue

        for juego in juegos_de_esa_tag:
            appid = str(juego.get("appid", "")).strip()
            if not appid:
                continue

            if appid in appids_usuario:
                continue

            nombre = juego.get("name", "Sin nombre")
            positive = int(juego.get("positive", 0) or 0)
            relevancia = float(juego.get("relevancia", 0) or 0)

            if appid not in candidatos:
                candidatos[appid] = {
                    "appid": appid,
                    "name": nombre,
                    "positive": positive,
                    "tags_coincidentes": set(),
                    "relevancia_total": 0.0,
                    "relevancia_max": 0.0,
                }

            candidatos[appid]["tags_coincidentes"].add(tag)
            candidatos[appid]["relevancia_total"] += relevancia
            candidatos[appid]["relevancia_max"] = max(
                candidatos[appid]["relevancia_max"],
                relevancia
            )
            candidatos[appid]["positive"] = max(
                candidatos[appid]["positive"],
                positive
            )

    recomendaciones = []

    for juego in candidatos.values():
        juego["coincidencias"] = len(juego["tags_coincidentes"])
        juego["tags_coincidentes"] = sorted(juego["tags_coincidentes"])
        recomendaciones.append(juego)

    recomendaciones.sort(
        key=lambda j: (
            -j["coincidencias"],
            -j["relevancia_total"],
            -j["relevancia_max"],
            -j["positive"],
            j["name"].lower()
        )
    )

    return tags_usuario, recomendaciones[:top_recomendaciones], tags_sin_json


def mostrar_recomendaciones(
    lista_juegos,
    carpeta_tags=CARPETA_TAGS,
    num_tags_por_juego=5,
    top_tags_usuario=5,
    top_recomendaciones=5
):
    """
    Muestra por consola:
    - las top tags del usuario
    - las 5 mejores recomendaciones basadas en coincidencias de tags
    """
    tags_usuario, recomendaciones, tags_sin_json = recomendar_juegos_desde_json(
        lista_juegos=lista_juegos,
        carpeta_tags=carpeta_tags,
        num_tags_por_juego=num_tags_por_juego,
        top_tags_usuario=top_tags_usuario,
        top_recomendaciones=top_recomendaciones
    )

    if not tags_usuario:
        print("No se pudieron obtener tags del usuario.")
        return

    print("-" * 60)
    print("TOP TAGS DEL USUARIO:\n")
    for i, tag in enumerate(tags_usuario, 1):
        print(f"{i}. {tag}")

    if tags_sin_json:
        print("\nTags sin JSON asociado:")
        for tag in tags_sin_json:
            print(f"- {tag}")

    print("\n" + "-" * 60)
    print("RECOMENDACIONES:\n")

    if not recomendaciones:
        print("No se encontraron recomendaciones con las tags disponibles.")
        return

    for i, juego in enumerate(recomendaciones, 1):
        tags_txt = ", ".join(juego["tags_coincidentes"])
        print(f"{i}. {juego['name']} (AppID: {juego['appid']})")
        print(f"   Coincidencias de tags: {juego['coincidencias']}")
        print(f"   Tags comunes: {tags_txt}")
        print(f"   Relevancia total: {juego['relevancia_total']:.2f}")
        print(f"   Positive: {juego['positive']}")
        print()


if __name__ == "__main__":
    steam_id = "76561199116601828"

    if API_KEY == "TU_API_KEY_AQUI":
        print("Debes sustituir TU_API_KEY_AQUI por tu API key real en saca_biblioteca.py")
    else:
        lista_juegos = crear_lista_juegos_desde_steam(steam_id, API_KEY)
        mostrar_recomendaciones(
            lista_juegos,
            carpeta_tags=CARPETA_TAGS,
            num_tags_por_juego=5,
            top_tags_usuario=5,
            top_recomendaciones=5
        )