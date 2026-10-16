(() => {
  const tabs = [...document.querySelectorAll('[data-profile-tab]')];
  const selectTab = (name, focus = false) => {
    tabs.forEach(tab => {
      const active = tab.dataset.profileTab === name;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      document.querySelector(`#panel-${tab.dataset.profileTab}`).hidden = !active;
      if (active && focus) tab.focus();
    });
    const url = new URL(window.location.href);
    url.searchParams.set('tab', name);
    window.history.replaceState(null, '', url);
  };
  tabs.forEach((tab, index) => {
    tab.tabIndex = tab.getAttribute('aria-selected') === 'true' ? 0 : -1;
    tab.addEventListener('click', () => selectTab(tab.dataset.profileTab));
    tab.addEventListener('keydown', event => {
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
        event.preventDefault();
        const next = tabs[(index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
        selectTab(next.dataset.profileTab, true);
      }
    });
  });
  document.querySelectorAll('[data-password-toggle]').forEach(button => {
    button.addEventListener('click', () => {
      const field = document.getElementById(button.dataset.passwordToggle);
      const showing = field.type === 'password';
      field.type = showing ? 'text' : 'password';
      button.textContent = showing ? 'Ẩn' : 'Hiện';
      button.setAttribute('aria-pressed', String(showing));
      button.setAttribute('aria-label', `${showing ? 'Ẩn' : 'Hiện'} ${field.closest('label').childNodes[0].textContent.trim().toLowerCase()}`);
    });
  });
  const bio = document.querySelector('#profile-bio');
  const counter = document.querySelector('#bio-count');
  const countBio = () => { if (counter && bio) counter.textContent = Array.from(bio.value).length; };
  bio?.addEventListener('input', countBio);
  countBio();
  const picker = document.querySelector('#avatar-input');
  document.querySelector('[data-avatar-picker]')?.addEventListener('click', () => picker.click());
  picker?.addEventListener('change', () => {
    const file = picker.files[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      document.querySelector('#avatar-error').textContent = 'Ảnh không được vượt quá 10 MB.';
      picker.value = '';
      return;
    }
    document.querySelector('#avatar-form').requestSubmit();
  });
})();
