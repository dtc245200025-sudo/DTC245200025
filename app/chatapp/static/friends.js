(() => {
  const page = document.querySelector('[data-friends-page]');
  const content = document.querySelector('#friends-content');
  const status = document.querySelector('#friends-update-status');
  const socket = window.linhSocket;
  let version = 0;
  async function refreshPanel() {
    const current = ++version;
    const body = new URLSearchParams({
      view: page.dataset.view,
      q: page.dataset.query,
      csrf_token: document.querySelector('#friend-search-form [name="csrf_token"]').value
    });
    try {
      const response = await fetch('/friends/panel', {method: 'POST', body, credentials: 'same-origin', cache: 'no-store'});
      if (response.redirected || response.status === 401) { window.location.assign('/login'); return; }
      if (!response.ok) throw new Error('refresh failed');
      const html = await response.text();
      if (current !== version) return;
      content.innerHTML = html;
      window.linhRefreshPresence?.();
      status.textContent = '';
    } catch { if (current === version) status.textContent = 'Chưa cập nhật được danh sách. Bạn có thể tải lại trang.'; }
  }
  socket.on('friends_changed', refreshPanel);
  socket.on('connect', refreshPanel);
  if (socket.connected) refreshPanel();
  document.addEventListener('submit', event => {
    if (event.target.matches('[data-remove-friend]') && !window.confirm('Hủy kết bạn với người này? Lịch sử phòng chat vẫn được giữ.')) event.preventDefault();
  });
})();
