(() => {
  let theme = 'light';
  try { theme = localStorage.getItem('linhchat-theme') === 'dark' ? 'dark' : 'light'; } catch {}
  const apply = () => {
    document.documentElement.dataset.theme = theme;
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.textContent = theme === 'dark' ? '☀ Chế độ sáng' : '☾ Chế độ tối';
      button.setAttribute('aria-pressed', String(theme === 'dark'));
    });
  };
  apply();
  document.addEventListener('DOMContentLoaded', () => {
    apply();
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => {
        theme = theme === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem('linhchat-theme', theme); } catch {}
        apply();
      });
    });
  });
  window.addEventListener('storage', event => {
    if (event.key === 'linhchat-theme') {
      theme = event.newValue === 'dark' ? 'dark' : 'light';
      apply();
    }
  });
})();
