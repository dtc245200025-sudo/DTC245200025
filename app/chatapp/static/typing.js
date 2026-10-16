(() => {
  window.createLinhTyping = ({scope, targetId, input, indicator, currentUser}) => {
    const socket = window.linhSocket;
    const remote = new Map();
    let idleTimer, lastSent = 0, active = false;
    const render = () => {
      const names = [...remote.values()].map(item => item.name);
      indicator.textContent = names.length ? `${names.slice(0, 2).join(', ')}${names.length > 2 ? ` và ${names.length - 2} người khác` : ''} đang nhập…` : '';
    };
    const clear = () => { remote.forEach(item => clearTimeout(item.timer)); remote.clear(); render(); };
    const stop = () => {
      clearTimeout(idleTimer);
      if (active && socket.connected) socket.emit('typing', {scope, target_id: targetId, typing: false});
      active = false;
      lastSent = 0;
    };
    input.addEventListener('input', () => {
      clearTimeout(idleTimer);
      if (!socket.connected || !input.value.trim() || input.disabled || document.hidden) { stop(); return; }
      const now = Date.now();
      if (!active || now - lastSent >= 1000) {
        socket.emit('typing', {scope, target_id: targetId, typing: true});
        active = true;
        lastSent = now;
      }
      idleTimer = setTimeout(stop, 1800);
    });
    input.addEventListener('blur', stop);
    document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
    window.addEventListener('pagehide', stop);
    socket.on('typing', data => {
      if (data.scope !== scope || data.target_id !== targetId || data.user_id === currentUser) return;
      clearTimeout(remote.get(data.user_id)?.timer);
      remote.delete(data.user_id);
      if (data.typing) remote.set(data.user_id, {name: data.name, timer: setTimeout(() => { remote.delete(data.user_id); render(); }, 4000)});
      render();
    });
    socket.on('disconnect', () => { active = false; clearTimeout(idleTimer); clear(); });
    return {stop, clear};
  };
})();
