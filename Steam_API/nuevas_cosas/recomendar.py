import requests
from math import ceil
from collections import Counter
from saca_biblioteca import crear_lista_juegos_desde_steam, API_KEY

STEAMSPY_URL = "https://steamspy.com/api.php"


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


def mostrar_top_tags_frecuentes(lista_juegos, num_tags_por_juego=5, top_n=5):
    """
    Muestra por consola las tags más frecuentes entre los juegos relevantes.
    """
    contador_tags = recolectar_tags_frecuentes(lista_juegos, num_tags_por_juego=num_tags_por_juego)

    if not contador_tags:
        print("No se pudieron obtener tags de los juegos seleccionados.")
        return

    print("-" * 60)

    for i, (tag, frecuencia) in enumerate(contador_tags.most_common(top_n), 1):
        print(f"{i}. {tag}")


if __name__ == "__main__":
    steam_id = "76561199116601828"

    if API_KEY == "TU_API_KEY_AQUI":
        print("Debes sustituir TU_API_KEY_AQUI por tu API key real en saca_biblioteca.py")
    else:
        lista_juegos = crear_lista_juegos_desde_steam(steam_id, API_KEY)
        mostrar_top_tags_frecuentes(lista_juegos, num_tags_por_juego=5, top_n=5)