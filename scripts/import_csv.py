import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "games_steam.csv"
DB_PATH = BASE_DIR / "steam_games.db"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"

def to_int_bool(value):
    if value is None:
        return 0
    v = str(value).strip().lower()
    return 1 if v == "true" else 0

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

def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"No se encuentra el CSV: {CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Crear tabla
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    cur.executescript(schema_sql)

    insert_sql = """
    INSERT INTO games (
        appid, name, release_date, price, short_description, header_image,
        windows, mac, linux, supported_languages, developers, publishers,
        categories, genres, positive, negative, average_playtime_forever,
        median_playtime_forever, discount, tags
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append((
                to_int(r.get("appid")),
                r.get("name", ""),
                r.get("release_date", ""),
                to_float(r.get("price")),
                r.get("short_description", ""),
                r.get("header_image", ""),
                to_int_bool(r.get("windows")),
                to_int_bool(r.get("mac")),
                to_int_bool(r.get("linux")),
                r.get("supported_languages", ""),   # guardado como texto (lista en string)
                r.get("developers", ""),            # guardado como texto
                r.get("publishers", ""),            # guardado como texto
                r.get("categories", ""),            # guardado como texto
                r.get("genres", ""),                # guardado como texto
                to_int(r.get("positive")),
                to_int(r.get("negative")),
                to_int(r.get("average_playtime_forever")),
                to_int(r.get("median_playtime_forever")),
                to_int(r.get("discount")),
                r.get("tags", "")                   # dict en string
            ))

    cur.executemany(insert_sql, rows)
    conn.commit()

    # Comprobación rápida
    cur.execute("SELECT COUNT(*) FROM games")
    total = cur.fetchone()[0]
    print(f"Importación completada. Juegos insertados: {total}")
    print(f"BD creada en: {DB_PATH}")

    conn.close()

if __name__ == "__main__":
    main()