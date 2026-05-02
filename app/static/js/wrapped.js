document.addEventListener('DOMContentLoaded', () => {
  const tags = document.querySelectorAll('.wrapped-filter-tag');
  const topGamesContainer = document.getElementById('top-games-container');
  const achievementsContainer = document.getElementById('achievements-container');
  const topGamesTitle = document.getElementById('top-games-title');
  const achievementsTitle = document.getElementById('achievements-title');
  
  if (!window.WRAPPED_CONFIG) return;
  const { steamId, filterRoute } = window.WRAPPED_CONFIG;

  const defaultTopGamesHTML = topGamesContainer.innerHTML;
  const defaultAchievementsHTML = achievementsContainer.innerHTML;
  
  let activeTag = null;

  tags.forEach(tagEl => {
    tagEl.addEventListener('click', async () => {
      const tag = tagEl.dataset.tag;

      // Deselect logic
      if (activeTag === tag) {
        activeTag = null;
        tags.forEach(t => t.style.boxShadow = 'none');
        topGamesTitle.textContent = 'Top Games';
        achievementsTitle.textContent = 'Achievements';
        topGamesContainer.innerHTML = defaultTopGamesHTML;
        achievementsContainer.innerHTML = defaultAchievementsHTML;
        return;
      }

      // Highlight the active tag visually
      activeTag = tag;
      tags.forEach(t => t.style.boxShadow = 'none');
      tagEl.style.boxShadow = '0 0 10px rgba(255,215,0, 0.6)';
      
      // Loaders
      topGamesTitle.textContent = `Top Games (${tag})`;
      achievementsTitle.textContent = `Achievements (${tag})`;
      
      const loaderHTML = `<div class="d-flex justify-content-center pt-4"><div class="spinner-border text-light" role="status"></div></div>`;
      topGamesContainer.innerHTML = loaderHTML;
      achievementsContainer.innerHTML = loaderHTML;

      try {
        const response = await fetch(`${filterRoute}?steamId=${encodeURIComponent(steamId)}&tag=${encodeURIComponent(tag)}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        // Render Top Games
        if (data.topGames && data.topGames.length > 0) {
          topGamesContainer.innerHTML = data.topGames.map(g => `
            <div class="list-group-item d-flex align-items-center gap-3 flex-wrap">
              <img src="${g.image}" alt="${escapeHtml(g.name)}" class="game-thumb" width="140" height="40" onerror="this.src='https://via.placeholder.com/140x40?text=NA'" />
              <div class="flex-grow-1">
                <div class="fw-bold"><a href="https://store.steampowered.com/app/${g.appid}/" target="_blank" rel="noopener noreferrer" class="link-info text-decoration-underline">${escapeHtml(g.name)}</a></div>
                <div class="text-white small">${g.playtime_hours} h</div>
              </div>
            </div>
          `).join('');
        } else {
          topGamesContainer.innerHTML = `<div class="empty-results mt-2">No tienes juegos de este tag en tu biblioteca reciente.</div>`;
        }

        // Render Achievements
        if (data.achievements && data.achievements.length > 0) {
          achievementsContainer.innerHTML = data.achievements.map(group => {
            const percentageBadge = `<span class="badge" style="background-color: rgba(43, 121, 255, 0.4); border: 1px solid rgba(43, 121, 255, 0.6); font-size: 0.8em;">${group.percentage}% (${group.total_obtained}/${group.total})</span>`;
            
            let rarestHtml = '';
            if (group.rarest && group.rarest.length > 0) {
              rarestHtml = `<div class="d-flex flex-column gap-2 mt-1">` + 
                group.rarest.map(a => `
                  <div class="p-2 rounded border" style="background-color: rgba(0,0,0,0.25); border-color: rgba(255,255,255,0.08) !important;">
                    <div class="d-flex align-items-center gap-2 mb-1">
                      ${a.icon ? `<img src="/static/img/${a.icon}" alt="${a.icon}" width="24" height="24" style="object-fit: contain;">` : ''}
                      <div class="fw-bold text-white" style="font-size: 0.9rem;">${escapeHtml(a.name)}</div>
                    </div>
                    <div class="text-white-50" style="font-size: 0.8rem; line-height: 1.3;">${escapeHtml(a.description)}</div>
                  </div>
                `).join('') + `</div>`;
            } else {
              rarestHtml = `<div class="text-white-50 small mt-1">Aún no hay logros obtenidos en este juego.</div>`;
            }

            return `
              <div class="list-group-item d-flex flex-column gap-2 p-3 mb-2" style="background-color: rgba(255,255,255,0.03); border-radius: 12px;">
                <div class="d-flex justify-content-between align-items-center">
                  <strong class="text-white fs-6">${escapeHtml(group.game_name)}</strong>
                  ${percentageBadge}
                </div>
                ${rarestHtml}
              </div>
            `;
          }).join('');
        } else {
          achievementsContainer.innerHTML = `<div class="empty-results mt-2">No se encontraron logros en estos juegos.</div>`;
        }
      } catch (error) {
        console.error('Error filtering wrapped details:', error);
        topGamesContainer.innerHTML = `<div class="error-box">Error al cargar datos filtrados.</div>`;
        achievementsContainer.innerHTML = `<div class="error-box">Error al cargar datos filtrados.</div>`;
      }
    });
  });
  
  function escapeHtml(text) {
    if (!text) return "";
    return String(text).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[char]));
  }
});
