(() => {
  const socket = window.linhSocket;
  const region = document.querySelector('#message-notifications');
  if (!socket || !region) return;
  const originalTitle = document.title;
  const seenEvents = new Set();
  let running = false, dirty = false, retryTimer;
  function badge(element, count) {
    element.hidden = !count;
    element.textContent = count > 99 ? '99+' : String(count);
    element.setAttribute('aria-label', `${count} tin chưa đọc`);
  }
  async function refresh() {
    dirty = true;
    if (running) return;
    running = true;
    clearTimeout(retryTimer);
    try {
      do {
        dirty = false;
        const response = await fetch('/notifications/state', {cache: 'no-store'});
        if (response.redirected) { window.location.assign('/login'); return; }
        if (!response.ok) throw new Error('unread');
        const state = await response.json();
        document.querySelectorAll('[data-unread-total]').forEach(element => badge(element, state[`${element.dataset.unreadTotal}_total`] || 0));
        document.querySelectorAll('[data-unread-direct]').forEach(element => badge(element, state.directs[element.dataset.unreadDirect] || 0));
        document.querySelectorAll('[data-unread-room]').forEach(element => badge(element, state.rooms[element.dataset.unreadRoom] || 0));
        document.title = state.total ? `(${state.total}) ${originalTitle}` : originalTitle;
        // Remove a toast if this or another tab has already viewed its chat.
        region.querySelectorAll('[data-notification-scope]').forEach(element => {
          const counts = element.dataset.notificationScope === 'room' ? state.rooms : state.directs;
          if (!counts[element.dataset.notificationTarget]) element.remove();
        });
      } while (dirty);
    } catch {
      retryTimer = setTimeout(refresh, 5000);
    } finally { running = false; }
  }
  function viewing(data) {
    const root = document.querySelector('[data-conversation]');
    if (document.visibilityState !== 'visible' || !document.hasFocus() || !root ||
        root.dataset.scope !== data.scope || Number(root.dataset.targetId) !== data.target_id ||
        document.querySelector('#chat-message-details')?.open) return false;
    const messages = root.querySelector('.direct-messages');
    if (!messages) return false;
    const bounds = messages.getBoundingClientRect();
    return bounds.bottom > 0 && bounds.top < innerHeight &&
      messages.scrollHeight - messages.scrollTop - messages.clientHeight < 90;
  }
  socket.on('message_notification', data => {
    const key = `${data.scope}:${data.message_id}`;
    if (seenEvents.has(key)) return;
    seenEvents.add(key);
    if (seenEvents.size > 500) seenEvents.delete(seenEvents.values().next().value);
    // Delivery is acknowledged by app.js for the full message, not this preview.
    refresh();
    if (viewing(data)) return;
    const toast = document.createElement('article');
    toast.className = 'message-notification';
    toast.dataset.notificationScope = data.scope;
    toast.dataset.notificationTarget = data.target_id;
    const heading = document.createElement('strong'); heading.textContent = `${data.sender} · ${data.title}`;
    const preview = document.createElement('p'); preview.textContent = data.preview;
    const link = document.createElement('a'); link.textContent = 'Xem tin nhắn →'; link.href = data.url;
    const close = document.createElement('button'); close.type = 'button'; close.className = 'notification-close secondary';
    close.textContent = '×'; close.setAttribute('aria-label', 'Đóng thông báo');
    close.addEventListener('click', () => toast.remove());
    toast.append(heading, preview, link, close);
    region.append(toast);
    while (region.children.length > 3) region.firstElementChild.remove();
    // Dismissing the popup never marks a message as read.
    setTimeout(() => { if (!toast.matches(':hover') && !toast.contains(document.activeElement)) toast.remove(); }, 15000);
  });
  socket.on('unread_changed', refresh);
  socket.on('connect', refresh);
  socket.on('direct_changed', () => setTimeout(refresh, 150));
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  window.addEventListener('focus', refresh);
  window.linhRefreshUnread = refresh;
  if (socket.connected) refresh();
})();
