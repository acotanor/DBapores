(() => {
  const DEMO_STEAM_ID = '76561199116601828';

  const form = document.getElementById('steamForm');
  const steamIdInput = document.getElementById('steamId');
  const loadingState = document.getElementById('loadingState');
  const errorState = document.getElementById('errorState');
  const resultState = document.getElementById('resultState');
  const resultsSummary = document.getElementById('resultsSummary');
  const resultsGrid = document.getElementById('resultsGrid');
  const submitBtn = document.getElementById('submitBtn');
  const demoBtn = document.getElementById('demoBtn');

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
        <h2>Tus gustos detectados</h2>
        <div class="tag-list">
          ${topTags.map((tag) => `<span class="tag-pill">${escapeHtml(tag)}</span>`).join('') || '<span class="tag-pill">Sin tags</span>'}
        </div>
        ${missingTagFiles.length ? `<p class="muted-note">Faltan archivos JSON para: ${escapeHtml(missingTagFiles.join(', '))}</p>` : ''}
      </section>
    `;

    if (!recommendations.length) {
      resultsGrid.innerHTML = `
        <div class="empty-results">
          No se han encontrado recomendaciones con las tags disponibles en <strong>tags/</strong>.
        </div>
      `;
      return;
    }

    resultsGrid.innerHTML = recommendations.map((game, index) => {
      const matchingTags = Array.isArray(game.tagsCoincidentes) ? game.tagsCoincidentes : [];
      const reason = matchingTags.length
        ? `Porque encaja con tus gustos en: ${escapeHtml(matchingTags.join(', '))}.`
        : 'Porque encaja con los gustos detectados en tu biblioteca.';

      return `
        <article class="result-card">
          <div class="result-rank">${index + 1}</div>
          <h3>${escapeHtml(game.name || 'Juego sin nombre')}</h3>
          <p>${reason}</p>
          <a class="result-link" href="${escapeAttribute(game.steamUrl || '#')}" target="_blank" rel="noopener noreferrer">
            Ver en Steam
          </a>
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

  async function fetchRecommendations(steamId) {
    const response = await fetch(`/api/recommend?steamId=${encodeURIComponent(steamId)}`);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }

    return data;
  }

  demoBtn.addEventListener('click', () => {
    steamIdInput.value = DEMO_STEAM_ID;
    form.requestSubmit();
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const steamId = steamIdInput.value.trim();

    if (!/^\d{17}$/.test(steamId)) {
      setState({
        loading: false,
        error: 'Introduce un SteamID64 válido de 17 dígitos.',
        payload: null
      });
      steamIdInput.focus();
      return;
    }

    setState({ loading: true, error: '', payload: null });

    try {
      const payload = await fetchRecommendations(steamId);
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
