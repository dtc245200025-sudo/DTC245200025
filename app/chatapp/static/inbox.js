(() => {
  const page = document.querySelector('[data-direct-page]');
  const socket = window.linhSocket;
  const conversationId = Number(page.dataset.conversationId || 0);
  let version = 0;
  async function refresh() {
    const current = ++version;
    try {
      const response = await fetch('/direct/panel', {cache: 'no-store'});
      if (response.redirected) { window.location.assign('/login'); return; }
      if (!response.ok) throw new Error('inbox');
      const html = await response.text();
      if (current !== version) return;
      const inbox = document.querySelector('#direct-inbox');
      inbox.innerHTML = html;
      inbox.querySelector(`[data-direct-thread="${conversationId}"]`)?.classList.add('is-current');
      window.linhRefreshPresence?.();
      window.linhRefreshUnread?.();
      document.querySelector('#inbox-update-status').textContent = '';
    } catch { document.querySelector('#inbox-update-status').textContent = 'Chưa cập nhật được danh sách.'; }
  }
  socket.on('direct_changed', refresh); socket.on('connect', refresh);
  if (socket.connected) refresh();
})();
