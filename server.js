const express = require('express');
const fs = require('fs/promises');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const BASE_DIR = __dirname;
const TAGS_DIR = path.join(BASE_DIR, 'tags');
const STEAM_API_KEY = process.env.STEAM_API_KEY || 'TU_API_KEY_AQUI';

const STEAM_API_BASE_URL = 'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/';
const STEAMSPY_URL = 'https://steamspy.com/api.php';

const steamSpyCache = new Map();
const tagFileCache = new Map();

app.use('/css', express.static(path.join(BASE_DIR, 'css')));
app.use('/js', express.static(path.join(BASE_DIR, 'js')));

app.get('/', (_req, res) => {
  res.sendFile(path.join(BASE_DIR, 'index.html'));
});

app.get('/index.html', (_req, res) => {
  res.sendFile(path.join(BASE_DIR, 'index.html'));
});

app.get('/opcion1.html', (_req, res) => {
  res.sendFile(path.join(BASE_DIR, 'opcion1.html'));
});

app.get('/logo.png', (_req, res) => {
  res.sendFile(path.join(BASE_DIR, 'logo.png'));
});

app.get('/api/recommend', async (req, res) => {
  try {
    const steamId = String(req.query.steamId || '').trim();

    if (!/^\d{17}$/.test(steamId)) {
      return res.status(400).json({
        error: 'El Steam ID debe ser un SteamID64 de 17 dígitos.'
      });
    }

    if (STEAM_API_KEY === 'TU_API_KEY_AQUI') {
      return res.status(500).json({
        error: 'Falta configurar la Steam API Key en server.js o en la variable de entorno STEAM_API_KEY.'
      });
    }

    const ownedGames = await getOwnedGames(steamId, STEAM_API_KEY);

    if (!ownedGames.length) {
      return res.status(404).json({
        error: 'No se ha podido leer la biblioteca. Revisa que el Steam ID sea correcto y que el perfil/juegos sean públicos.'
      });
    }

    const relevantGames = getRelevantGames(ownedGames);
    const tagCounter = await collectFrequentTags(relevantGames, 5);
    const topTags = getTopTags(tagCounter, 5);

    if (!topTags.length) {
      return res.status(404).json({
        error: 'No se pudieron obtener tags suficientes desde SteamSpy para generar recomendaciones.'
      });
    }

    const { recommendations, missingTagFiles } = await recommendGamesFromLocalTags({
      ownedGames,
      topTags,
      tagsDir: TAGS_DIR,
      limit: 5
    });

    return res.json({
      steamId,
      topTags,
      missingTagFiles,
      recommendations,
      stats: {
        totalOwnedGames: ownedGames.length,
        relevantGamesAnalyzed: relevantGames.length
      }
    });
  } catch (error) {
    console.error('Error en /api/recommend:', error);

    return res.status(500).json({
      error: 'Ha ocurrido un error interno al generar las recomendaciones.'
    });
  }
});

async function getOwnedGames(steamId, apiKey) {
  const url = new URL(STEAM_API_BASE_URL);
  url.searchParams.set('key', apiKey);
  url.searchParams.set('steamid', steamId);
  url.searchParams.set('include_appinfo', 'true');
  url.searchParams.set('include_played_free_games', 'true');
  url.searchParams.set('format', 'json');

  const response = await fetchWithTimeout(url.toString(), { timeoutMs: 20000 });

  if (!response.ok) {
    throw new Error(`Steam API respondió con HTTP ${response.status}`);
  }

  const data = await response.json();
  const games = data?.response?.games ?? [];

  return games.map((game) => ({
    appid: String(game.appid),
    name: game.name || 'Sin nombre',
    playtime_forever: Number(game.playtime_forever || 0),
    playtime_2weeks: Number(game.playtime_2weeks || 0),
    img_icon_url: game.img_icon_url || '',
    img_logo_url: game.img_logo_url || '',
    has_community_visible_stats: Boolean(game.has_community_visible_stats)
  }));
}

function getRelevantGames(games) {
  if (!Array.isArray(games) || !games.length) {
    return [];
  }

  const sortedGames = [...games].sort((a, b) => b.playtime_forever - a.playtime_forever);

  if (sortedGames.length < 30) {
    return sortedGames;
  }

  const amount = Math.ceil(sortedGames.length * 0.30);
  return sortedGames.slice(0, amount);
}

async function collectFrequentTags(games, tagsPerGame = 5) {
  const counter = new Map();

  await asyncPool(6, games, async (game) => {
    const tags = await getSteamSpyTags(game.appid, tagsPerGame);

    for (const tag of tags) {
      counter.set(tag, (counter.get(tag) || 0) + 1);
    }
  });

  return counter;
}

function getTopTags(counter, topN = 5) {
  return [...counter.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, topN)
    .map(([tag]) => tag);
}

async function getSteamSpyTags(appid, numTags = 5) {
  const cacheKey = `${appid}:${numTags}`;

  if (steamSpyCache.has(cacheKey)) {
    return steamSpyCache.get(cacheKey);
  }

  const url = new URL(STEAMSPY_URL);
  url.searchParams.set('request', 'appdetails');
  url.searchParams.set('appid', String(appid));

  try {
    const response = await fetchWithTimeout(url.toString(), { timeoutMs: 15000 });

    if (!response.ok) {
      steamSpyCache.set(cacheKey, []);
      return [];
    }

    const data = await response.json();
    const tagsObject = data?.tags;

    if (!tagsObject || typeof tagsObject !== 'object') {
      steamSpyCache.set(cacheKey, []);
      return [];
    }

    const tags = Object.entries(tagsObject)
      .sort((a, b) => Number(b[1]) - Number(a[1]))
      .slice(0, numTags)
      .map(([tagName]) => String(tagName).toLowerCase());

    steamSpyCache.set(cacheKey, tags);
    return tags;
  } catch (_error) {
    steamSpyCache.set(cacheKey, []);
    return [];
  }
}

async function recommendGamesFromLocalTags({ ownedGames, topTags, tagsDir, limit = 5 }) {
  const ownedIds = new Set(ownedGames.map((game) => String(game.appid)));
  const candidates = new Map();
  const missingTagFiles = [];

  for (const tag of topTags) {
    const tagGames = await loadTagGames(tag, tagsDir);

    if (!tagGames.length) {
      missingTagFiles.push(tag);
      continue;
    }

    for (const game of tagGames) {
      const appid = String(game?.appid || '').trim();

      if (!appid || ownedIds.has(appid)) {
        continue;
      }

      const name = game?.name || 'Sin nombre';
      const positive = Number(game?.positive || 0);
      const relevancia = Number(game?.relevancia || 0);

      if (!candidates.has(appid)) {
        candidates.set(appid, {
          appid,
          name,
          positive,
          coincidencias: 0,
          tagsCoincidentes: new Set(),
          relevancia_total: 0,
          relevancia_max: 0
        });
      }

      const candidate = candidates.get(appid);
      candidate.tagsCoincidentes.add(tag);
      candidate.relevancia_total += relevancia;
      candidate.relevancia_max = Math.max(candidate.relevancia_max, relevancia);
      candidate.positive = Math.max(candidate.positive, positive);
    }
  }

  const recommendations = [...candidates.values()]
    .map((candidate) => {
      const tagsCoincidentes = [...candidate.tagsCoincidentes].sort((a, b) => a.localeCompare(b));

      return {
        ...candidate,
        coincidencias: tagsCoincidentes.length,
        tagsCoincidentes,
        steamUrl: `https://store.steampowered.com/app/${candidate.appid}/`
      };
    })
    .sort((a, b) => {
      return (
        b.coincidencias - a.coincidencias ||
        b.relevancia_total - a.relevancia_total ||
        b.relevancia_max - a.relevancia_max ||
        b.positive - a.positive ||
        a.name.localeCompare(b.name)
      );
    })
    .slice(0, limit);

  return { recommendations, missingTagFiles };
}

async function loadTagGames(tag, tagsDir) {
  const fileName = `${normalizeTagToFileName(tag)}.json`;
  const filePath = path.join(tagsDir, fileName);

  if (tagFileCache.has(filePath)) {
    return tagFileCache.get(filePath);
  }

  try {
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const parsed = JSON.parse(fileContent);
    const games = Array.isArray(parsed) ? parsed : [];
    tagFileCache.set(filePath, games);
    return games;
  } catch (_error) {
    tagFileCache.set(filePath, []);
    return [];
  }
}

function normalizeTagToFileName(tag) {
  return String(tag)
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/&/g, 'and')
    .replace(/[ /-]+/g, '_')
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '');
}

async function asyncPool(limit, items, iteratorFn) {
  const ret = [];
  const executing = new Set();

  for (const item of items) {
    const promise = Promise.resolve().then(() => iteratorFn(item));
    ret.push(promise);
    executing.add(promise);

    const clean = () => executing.delete(promise);
    promise.then(clean).catch(clean);

    if (executing.size >= limit) {
      await Promise.race(executing);
    }
  }

  return Promise.allSettled(ret);
}

async function fetchWithTimeout(url, { timeoutMs = 15000 } = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}

app.listen(PORT, () => {
  console.log(`Servidor listo en http://localhost:${PORT}`);
});
