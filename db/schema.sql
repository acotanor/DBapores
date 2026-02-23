DROP TABLE IF EXISTS game_publishers;
DROP TABLE IF EXISTS game_developers;
DROP TABLE IF EXISTS game_languages;
DROP TABLE IF EXISTS game_tags;
DROP TABLE IF EXISTS game_genres;
DROP TABLE IF EXISTS games;

CREATE TABLE games (
    appid INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    release_date TEXT,
    price REAL DEFAULT 0,
    short_description TEXT,
    header_image TEXT,
    windows INTEGER DEFAULT 0,
    mac INTEGER DEFAULT 0,
    linux INTEGER DEFAULT 0,
    positive INTEGER DEFAULT 0,
    negative INTEGER DEFAULT 0,
    average_playtime_forever INTEGER DEFAULT 0,
    median_playtime_forever INTEGER DEFAULT 0,
    discount INTEGER DEFAULT 0
);

CREATE TABLE game_genres (
    appid INTEGER NOT NULL,
    genre TEXT NOT NULL,
    PRIMARY KEY (appid, genre),
    FOREIGN KEY (appid) REFERENCES games(appid) ON DELETE CASCADE
);

CREATE TABLE game_tags (
    appid INTEGER NOT NULL,
    tag TEXT NOT NULL,
    weight_raw INTEGER DEFAULT 0,          -- valor original del CSV
    weight_percent REAL DEFAULT 0,         -- porcentaje dentro del juego (0-100)
    PRIMARY KEY (appid, tag),
    FOREIGN KEY (appid) REFERENCES games(appid) ON DELETE CASCADE
);

CREATE TABLE game_languages (
    appid INTEGER NOT NULL,
    language TEXT NOT NULL,
    PRIMARY KEY (appid, language),
    FOREIGN KEY (appid) REFERENCES games(appid) ON DELETE CASCADE
);

CREATE TABLE game_developers (
    appid INTEGER NOT NULL,
    developer TEXT NOT NULL,
    PRIMARY KEY (appid, developer),
    FOREIGN KEY (appid) REFERENCES games(appid) ON DELETE CASCADE
);

CREATE TABLE game_publishers (
    appid INTEGER NOT NULL,
    publisher TEXT NOT NULL,
    PRIMARY KEY (appid, publisher),
    FOREIGN KEY (appid) REFERENCES games(appid) ON DELETE CASCADE
);

-- Índices útiles
CREATE INDEX idx_games_name ON games(name);
CREATE INDEX idx_games_price ON games(price);
CREATE INDEX idx_games_discount ON games(discount);
CREATE INDEX idx_games_release_date ON games(release_date);
CREATE INDEX idx_games_positive ON games(positive);

CREATE INDEX idx_game_genres_genre ON game_genres(genre);
CREATE INDEX idx_game_tags_tag ON game_tags(tag);
CREATE INDEX idx_game_tags_weight_raw ON game_tags(weight_raw);
CREATE INDEX idx_game_tags_weight_percent ON game_tags(weight_percent);
CREATE INDEX idx_game_languages_language ON game_languages(language);
CREATE INDEX idx_game_developers_developer ON game_developers(developer);
CREATE INDEX idx_game_publishers_publisher ON game_publishers(publisher);