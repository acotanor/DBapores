(() => {
  const DEMO_APP_ID = '730'; // CS:GO

  const form = document.getElementById('steamForm');
  const appIdInput = document.getElementById('appId');
  const loadingState = document.getElementById('loadingState');
  const errorState = document.getElementById('errorState');
  const resultState = document.getElementById('resultState');
  const resultsSummary = document.getElementById('resultsSummary');
  const resultsGrid = document.getElementById('resultsGrid');
  const submitBtn = document.getElementById('submitBtn');
  const demoBtn = document.getElementById('demoBtn');
  const datalist = document.getElementById('gameSuggestions');
  let searchTimeout;

  function setState({ loading = false, error = '', payload = null }) {
    loadingState.classList.toggle('d-none', !loading);

    const hasError = Boolean(error);
    errorState.classList.toggle('d-none', !hasError);
    errorState.textContent = error || '';

    const hasPayload = Boolean(payload);
    resultState.classList.toggle('d-none', !hasPayload);

    submitBtn.disabled = loading;
    demoBtn.disabled = loading;

    if (hasPayload) {
      renderPayload(payload);
    } else {
      resultsSummary.innerHTML = '';
      resultsGrid.innerHTML = '';
    }
  }

  function renderPayload(payload) {
    const topTags = Array.isArray(payload.topTags) ? payload.topTags : [];
    const recommendations = Array.isArray(payload.recommendations) ? payload.recommendations : [];
    const missingTagFiles = Array.isArray(payload.missingTagFiles) ? payload.missingTagFiles : [];

    resultsSummary.innerHTML = `
      <section class="summary-card">
        <h2>Tags del juego origen</h2>
        <div class="tag-list">
          ${topTags.map((tag) => `<span class="tag-pill">${escapeHtml(tag)}</span>`).join('') || '<span class="tag-pill">Sin tags</span>'}
        </div>
        ${missingTagFiles.length ? `<p class="muted-note">Faltan archivos JSON para: ${escapeHtml(missingTagFiles.join(', '))}</p>` : ''}
      </section>
    `;

    if (!recommendations.length) {
      resultsGrid.innerHTML = `
        <div class="empty-results">
          No se han encontrado juegos similares con las tags disponibles en <strong>tags/</strong>.
        </div>
      `;
      return;
    }

    resultsGrid.innerHTML = recommendations.map((game, index) => {
      const matchingTags = Array.isArray(game.tagsCoincidentes) ? game.tagsCoincidentes : [];
      const reason = matchingTags.length
        ? `Coincide en tags clave: ${escapeHtml(matchingTags.join(', '))}.`
        : 'Coincide con características generales del juego insertado.';

      const headerImage = `https://cdn.akamai.steamstatic.com/steam/apps/${game.appid}/header.jpg`;

      return `
        <article class="card h-100 game-card">
          <div class="card-header-badge">${index + 1}</div>
          <img src="${headerImage}" class="card-img-top" alt="${escapeAttribute(game.name)}" onerror="this.src='https://via.placeholder.com/460x215?text=Imagen+no+disponible'">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title text-white mb-2">${escapeHtml(game.name || 'Juego sin nombre')}</h5>
            <p class="card-text flex-grow-1">${reason}</p>
            <div class="mt-3">
              <a href="${escapeAttribute(game.steamUrl || '#')}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm w-100 custom-btn">
                Ver en Steam
              </a>
            </div>
          </div>
        </article>
      `;
    }).join('');
  }

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }[char]));
  }

  function escapeAttribute(text) {
    return escapeHtml(text).replace(/`/g, '&#096;');
  }

  async function fetchRecommendations(appId) {
    const response = await fetch(`/api/recommend_by_game?appId=${encodeURIComponent(appId)}`);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }

    return data;
  }

  appIdInput.addEventListener('input', (e) => {
    const q = e.target.value.trim();
    if (q.length < 2) {
      datalist.innerHTML = '';
      return;
    }
    
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      try {
        const response = await fetch(`/api/search_games?q=${encodeURIComponent(q)}`);
        if (!response.ok) return;
        const games = await response.json();
        datalist.innerHTML = games.map(g => `<option value="${escapeAttribute(g.name)}"></option>`).join('');
      } catch (err) {
        console.error("Autocomplete error:", err);
      }
    }, 300);
  });

  demoBtn.addEventListener('click', () => {
    appIdInput.value = DEMO_APP_ID;
    form.requestSubmit();
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const appId = appIdInput.value.trim();

    if (!appId) {
      setState({
        loading: false,
        error: 'Introduce un App ID o Nombre válido.',
        payload: null
      });
      appIdInput.focus();
      return;
    }

    setState({ loading: true, error: '', payload: null });

    try {
      const payload = await fetchRecommendations(appId);
      setState({ loading: false, error: '', payload });
    } catch (error) {
      setState({
        loading: false,
        error: error.message || 'No se pudo generar la recomendación.',
        payload: null
      });
    }
  });
})();
