DROP TABLE IF EXISTS games;

CREATE TABLE games (
    appid INTEGER PRIMARY KEY,
    name TEXT,
    release_date TEXT,
    price REAL,
    short_description TEXT,
    header_image TEXT,
    windows INTEGER,
    mac INTEGER,
    linux INTEGER,
    supported_languages TEXT,
    developers TEXT,
    publishers TEXT,
    categories TEXT,
    genres TEXT,
    positive INTEGER,
    negative INTEGER,
    average_playtime_forever INTEGER,
    median_playtime_forever INTEGER,
    discount INTEGER,
    tags TEXT
);

-- Índices útiles para recomendaciones/filtros
CREATE INDEX idx_games_name ON games(name);
CREATE INDEX idx_games_price ON games(price);
CREATE INDEX idx_games_discount ON games(discount);
CREATE INDEX idx_games_release_date ON games(release_date);
CREATE INDEX idx_games_positive ON games(positive);
CREATE INDEX idx_games_genres ON games(genres);