(() => {
  const DEMO_STEAM_ID = "76561199116601828";

  const form = document.getElementById("steamForm");
  const steamIdInput = document.getElementById("steamId");
  const loadingState = document.getElementById("loadingState");
  const errorState = document.getElementById("errorState");
  const resultState = document.getElementById("resultState");
  const resultsSummary = document.getElementById("resultsSummary");
  const resultsGrid = document.getElementById("resultsGrid");
  const promotedSection = document.getElementById("promotedSection");
  const promotedList = document.getElementById("promotedList");
  const submitBtn = document.getElementById("submitBtn");
  const demoBtn = document.getElementById("demoBtn");

  function setState({ loading = false, error = "", payload = null }) {
    loadingState.classList.toggle("d-none", !loading);

    const hasError = Boolean(error);
    errorState.classList.toggle("d-none", !hasError);
    errorState.textContent = error || "";

    const hasPayload = Boolean(payload);
    resultState.classList.toggle("d-none", !hasPayload);

    submitBtn.disabled = loading;
    demoBtn.disabled = loading;

    if (hasPayload) {
      renderPayload(payload);
    } else {
      resultsSummary.innerHTML = "";
      resultsGrid.innerHTML = "";
      if (promotedList) promotedList.innerHTML = "";
      if (promotedSection) promotedSection.classList.add("d-none");
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
          ${topTags.map((tag) => `<span class="tag-pill">${escapeHtml(tag)}</span>`).join("") ||
      '<span class="tag-pill">Sin tags</span>'
      }
        </div>
      </section>
    `;

    if (!recommendations.length) {
      resultsGrid.innerHTML = `
        <div class="empty-results">
          No se han encontrado recomendaciones con las tags disponibles en <strong>data/tags/</strong>.
        </div>
      `;
      return;
    }

    const allRecommendations = Array.isArray(payload.recommendations) ? payload.recommendations : [];
    const top5 = allRecommendations.slice(0, 5);
    const promos = allRecommendations.slice(5, 8);

    if (promos.length > 0 && promotedSection && promotedList) {
      promotedSection.classList.remove("d-none");
      promotedList.innerHTML = promos.map((game) => {
        const matchingTags = Array.isArray(game.tagsCoincidentes) ? game.tagsCoincidentes : [];
        const reason = matchingTags.length ? `Similar a tus gustos en: ${escapeHtml(matchingTags.join(", "))}` : "";
        const headerImage = `https://cdn.akamai.steamstatic.com/steam/apps/${game.appid}/header.jpg`;

        return `
          <div class="list-group-item d-flex align-items-center gap-3 flex-wrap p-2 shadow-sm" style="background-color: rgba(179, 136, 235, 0.05); border: 1px solid rgba(179, 136, 235, 0.25); border-radius: 8px;">
            <a href="${escapeAttribute(game.steamUrl || "#")}" target="_blank" rel="noopener noreferrer">
              <img src="${headerImage}" alt="${escapeAttribute(game.name)}" class="game-thumb" style="width: 140px; height: 65px; object-fit: cover; border-radius: 4px;" onerror="this.src='https://via.placeholder.com/140x65?text=NA'">
            </a>
            <div class="flex-grow-1">
              <div class="fw-bold">
                <a href="${escapeAttribute(game.steamUrl || "#")}" target="_blank" rel="noopener noreferrer" class="text-decoration-none" style="color: #b388eb;">
                  ${escapeHtml(game.name || "Juego sin nombre")}
                </a>
                <span class="badge ms-2" style="font-size: 0.65em; vertical-align: middle; background-color: rgba(179, 136, 235, 0.2); color: #b388eb; border: 1px solid rgba(179, 136, 235, 0.5);">Patrocinado</span>
              </div>
              <div class="small mt-1" style="color: rgba(255,255,255,0.7);">${reason}</div>
            </div>
          </div>
        `;
      }).join("");
    } else if (promotedSection) {
      promotedSection.classList.add("d-none");
    }

    resultsGrid.innerHTML = top5.map((game, index) => {
      const matchingTags = Array.isArray(game.tagsCoincidentes) ? game.tagsCoincidentes : [];
      const reason = matchingTags.length
        ? `Porque encaja con tus gustos en: ${escapeHtml(matchingTags.join(", "))}.`
        : "Porque encaja con los gustos detectados en tu biblioteca.";

      const headerImage = `https://cdn.akamai.steamstatic.com/steam/apps/${game.appid}/header.jpg`;

      return `
        <article class="card h-100 game-card">
          <div class="card-header-badge">${index + 1}</div>
          <img src="${headerImage}" class="card-img-top" alt="${escapeAttribute(game.name)}" onerror="this.src='https://via.placeholder.com/460x215?text=Imagen+no+disponible'">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title text-white mb-2">${escapeHtml(game.name || "Juego sin nombre")}</h5>
            <p class="card-text flex-grow-1">${reason}</p>
            <div class="mt-3">
              <a href="${escapeAttribute(game.steamUrl || "#")}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm w-100 custom-btn">
                Ver en Steam
              </a>
            </div>
          </div>
        </article>
      `;
    }).join("");
  }

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[char]));
  }

  function escapeAttribute(text) {
    return escapeHtml(text).replace(/`/g, "&#096;");
  }

  async function fetchRecommendations(steamId) {
    const response = await fetch(`${window.API_ROUTES.recommend}?steamId=${encodeURIComponent(steamId)}`);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }

    return data;
  }

  demoBtn.addEventListener("click", () => {
    steamIdInput.value = DEMO_STEAM_ID;
    form.requestSubmit();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const steamId = steamIdInput.value.trim();

    if (!/^\d{17}$/.test(steamId)) {
      setState({
        loading: false,
        error: "Introduce un SteamID válido de 17 dígitos.",
        payload: null
      });
      steamIdInput.focus();
      return;
    }

    setState({ loading: true, error: "", payload: null });

    try {
      const payload = await fetchRecommendations(steamId);
      setState({ loading: false, error: "", payload });
    } catch (error) {
      setState({
        loading: false,
        error: error.message || "No se pudo generar la recomendación.",
        payload: null
      });
    }
  });
})();