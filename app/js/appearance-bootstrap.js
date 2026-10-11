// Resolve the saved appearance before the first paint on companion pages.
(function () {
  let preference = 'dark';
  try { preference = localStorage.getItem('fluency_theme_preference_v1') || 'dark'; } catch (_) {}
  if (!['dark', 'light', 'system'].includes(preference)) preference = 'dark';
  const theme = preference === 'system'
    ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : preference;
  const root = document.documentElement;
  root.dataset.themePreference = preference;
  root.dataset.theme = theme;
  root.style.colorScheme = theme;
})();
