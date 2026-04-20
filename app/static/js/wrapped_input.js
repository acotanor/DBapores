(() => {
  const DEMO_STEAM_ID = '76561199116601828';

  const form = document.getElementById('wrappedForm');
  const steamIdInput = document.getElementById('steamId');
  const demoBtn = document.getElementById('demoBtn');
  const errorState = document.getElementById('errorState');
  const submitBtn = document.getElementById('submitBtn');

  function showError(msg) {
    errorState.classList.remove('d-none');
    errorState.textContent = msg;
  }

  function clearError() {
    errorState.classList.add('d-none');
    errorState.textContent = '';
  }

  demoBtn.addEventListener('click', () => {
    steamIdInput.value = DEMO_STEAM_ID;
    form.requestSubmit();
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    clearError();
    const steamId = steamIdInput.value.trim();

    if (!/^\d{17}$/.test(steamId)) {
      showError('Introduce un SteamID64 válido de 17 dígitos.');
      steamIdInput.focus();
      return;
    }

    submitBtn.disabled = true;
    // Navigate to the report page which renders HTML at /api/wrapped/<steamId>
    window.location.href = `/api/wrapped/${encodeURIComponent(steamId)}`;
  });
})();
