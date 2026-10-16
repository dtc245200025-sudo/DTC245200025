(() => {
  const wrap = document.querySelector('#profile-menu-wrap');
  const trigger = document.querySelector('#profile-menu-trigger');
  const menu = document.querySelector('#profile-menu');
  const closeMenu = (restoreFocus = false) => {
    if (!menu || !trigger) return;
    menu.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    if (restoreFocus) trigger.focus();
  };
  trigger?.addEventListener('click', () => {
    const opening = menu.hidden;
    menu.hidden = !opening;
    trigger.setAttribute('aria-expanded', String(opening));
    if (opening) menu.querySelector('[role="menuitem"]')?.focus();
  });
  document.addEventListener('click', event => {
    if (wrap && !wrap.contains(event.target)) closeMenu();
  });
  document.addEventListener('keydown', event => {
    if (!menu || menu.hidden) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      closeMenu(true);
    }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const items = [...menu.querySelectorAll('[role="menuitem"]')];
      const index = items.indexOf(document.activeElement);
      items[(index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
    }
  });

  const onlineIds = new Set();
  function showPresence() {
    document.querySelectorAll('[data-presence-user]').forEach(element => {
      const online = onlineIds.has(Number(element.dataset.presenceUser));
      element.classList.toggle('is-online', online);
      element.querySelector('[data-presence-text]').textContent = online ? 'Đang hoạt động' : 'Ngoại tuyến';
    });
  }
  window.linhRefreshPresence = showPresence;
  window.linhSocket = io({ transports: ['websocket', 'polling'] });
  const socket = window.linhSocket;
  const currentUserId = Number(document.body.dataset.currentUser || 0);
  // Delivery is a browser acknowledgement, not a guess based on presence.
  // Group and direct envelopes arrive even on another application page.
  function acknowledgeDelivery(data, scope, targetId) {
    if (data.receipts_tracked && data.user_id !== currentUserId && data.recipient_ids?.includes(currentUserId)) {
      socket.emit('message_receipt', {scope, target_id: targetId, message_ids: [data.id], kind: 'delivered'});
    }
  }
  socket.on('direct_message', data => acknowledgeDelivery(data, 'direct', data.conversation_id));
  socket.on('new_message', data => acknowledgeDelivery(data, 'room', data.room_id));
  socket.on('friends_changed', data => {
    document.querySelectorAll('[data-friend-request-count]').forEach(badge => {
      badge.textContent = String(data.incoming_count);
      badge.hidden = !data.incoming_count;
    });
  });
  socket.on('presence_snapshot', data => {
    onlineIds.clear();
    data.online_ids.forEach(id => onlineIds.add(Number(id)));
    showPresence();
  });
  socket.on('presence', data => {
    if (data.online) onlineIds.add(Number(data.user_id));
    else onlineIds.delete(Number(data.user_id));
    showPresence();
  });
  socket.on('disconnect', () => {
    document.querySelectorAll('[data-presence-user]').forEach(element => {
      element.classList.remove('is-online');
      element.querySelector('[data-presence-text]').textContent = 'Chưa có kết nối';
    });
  });
  let changingPassword = false;
  document.addEventListener('submit', event => {
    if (event.target.matches('[data-password-change]')) changingPassword = true;
  });
  socket.on('session_revoked', () => { if (!changingPassword) window.location.assign('/login'); });
})();
