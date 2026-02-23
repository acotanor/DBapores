import csv
import sqlite3
import ast
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "games_steam.csv"
DB_PATH = BASE_DIR / "steam_games.db"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"


def to_int_bool(value):
    if value is None:
        return 0
    return 1 if str(value).strip().lower() == "true" else 0


def to_int(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(value))
    except Exception:
        return default


def to_float(value, default=0.0):
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except Exception:
        return default


def parse_python_list(value):
    """
    Convierte strings tipo "['Action', 'RPG']" en lista Python.
    Si viene vacío o mal formado, devuelve [].
    """
    if value is None:
        return []
    text = str(value).strip()
    if text == "":
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
        return []
    except Exception:
        return []


def parse_python_dict(value):
    """
    Convierte strings tipo "{'FPS': 90857, 'Shooter': 65397}" en dict Python.
    Si viene vacío o mal formado, devuelve {}.
    """
    if value is None:
        return {}
    text = str(value).strip()
    if text == "":
        return {}
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, dict):
            clean = {}
            for k, v in parsed.items():
                key = str(k).strip()
                if not key:
                    continue
                clean[key] = to_int(v, 0)
            return clean
        return {}
    except Exception:
        return {}


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"No se encuentra el CSV: {CSV_PATH}")
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No se encuentra el schema: {SCHEMA_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # Crear esquema desde cero
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    cur.executescript(schema_sql)

    insert_game_sql = """
    INSERT INTO games (
        appid, name, release_date, price, short_description, header_image,
        windows, mac, linux, positive, negative, average_playtime_forever,
        median_playtime_forever, discount
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    insert_genre_sql = """
    INSERT OR IGNORE INTO game_genres (appid, genre)
    VALUES (?, ?)
    """

    insert_tag_sql = """
    INSERT OR IGNORE INTO game_tags (appid, tag, weight_raw, weight_percent)
    VALUES (?, ?, ?, ?)
    """

    insert_language_sql = """
    INSERT OR IGNORE INTO game_languages (appid, language)
    VALUES (?, ?)
    """

    insert_developer_sql = """
    INSERT OR IGNORE INTO game_developers (appid, developer)
    VALUES (?, ?)
    """

    insert_publisher_sql = """
    INSERT OR IGNORE INTO game_publishers (appid, publisher)
    VALUES (?, ?)
    """

    game_rows = []
    genre_rows = []
    tag_rows = []
    language_rows = []
    developer_rows = []
    publisher_rows = []

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for r in reader:
            appid = to_int(r.get("appid"))
            if appid == 0:
                continue

            # Tabla principal
            game_rows.append((
                appid,
                (r.get("name") or "").strip(),
                (r.get("release_date") or "").strip(),
                to_float(r.get("price")),
                (r.get("short_description") or "").strip(),
                (r.get("header_image") or "").strip(),
                to_int_bool(r.get("windows")),
                to_int_bool(r.get("mac")),
                to_int_bool(r.get("linux")),
                to_int(r.get("positive")),
                to_int(r.get("negative")),
                to_int(r.get("average_playtime_forever")),
                to_int(r.get("median_playtime_forever")),
                to_int(r.get("discount")),
            ))

            # Tablas normalizadas (listas)
            genres = parse_python_list(r.get("genres"))
            languages = parse_python_list(r.get("supported_languages"))
            developers = parse_python_list(r.get("developers"))
            publishers = parse_python_list(r.get("publishers"))

            for genre in genres:
                genre_rows.append((appid, genre))

            for language in languages:
                language_rows.append((appid, language))

            for developer in developers:
                developer_rows.append((appid, developer))

            for publisher in publishers:
                publisher_rows.append((appid, publisher))

            # Tags con porcentaje por juego
            tags_dict = parse_python_dict(r.get("tags"))
            total_tag_weight = sum(v for v in tags_dict.values() if isinstance(v, int) and v > 0)

            for tag, raw_weight in tags_dict.items():
                if total_tag_weight > 0:
                    weight_percent = (raw_weight / total_tag_weight) * 100.0
                else:
                    weight_percent = 0.0

                # redondeo para guardar más limpio
                weight_percent = round(weight_percent, 6)

                tag_rows.append((appid, tag, raw_weight, weight_percent))

    # Inserción masiva
    cur.executemany(insert_game_sql, game_rows)
    cur.executemany(insert_genre_sql, genre_rows)
    cur.executemany(insert_tag_sql, tag_rows)
    cur.executemany(insert_language_sql, language_rows)
    cur.executemany(insert_developer_sql, developer_rows)
    cur.executemany(insert_publisher_sql, publisher_rows)

    conn.commit()

    # Resumen
    def count(table_name):
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cur.fetchone()[0]

    print("Importación completada:")
    print(f"  games:            {count('games')}")
    print(f"  game_genres:      {count('game_genres')}")
    print(f"  game_tags:        {count('game_tags')}")
    print(f"  game_languages:   {count('game_languages')}")
    print(f"  game_developers:  {count('game_developers')}")
    print(f"  game_publishers:  {count('game_publishers')}")
    print(f"\nBD creada en: {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    main()