(() => {
  const key = 'linhchat.pendingRoomInvite';
  let token = window.location.hash.slice(1);
  // Fragments are not sent in HTTP access logs. Retain the token only in this
  // tab until sign-in is complete, and remove it from the address bar.
  if (token) {
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) token = '';
    window.history.replaceState(null, '', window.location.pathname);
    try { if (token) sessionStorage.setItem(key, token); else sessionStorage.removeItem(key); } catch {}
  } else {
    try { token = sessionStorage.getItem(key) || ''; } catch {}
  }
  if (!token) return;
  document.querySelector('#invite-status').textContent = 'Đã nhận link mời. Đăng nhập nếu cần, rồi bấm tham gia để xác nhận quyền truy cập.';
  const input = document.querySelector('#invite-token');
  if (input) {
    input.value = token;
    document.querySelector('#invite-submit').disabled = false;
  }
  document.querySelector('#invite-join-form')?.addEventListener('submit', () => {
    try { sessionStorage.removeItem(key); } catch {}
  });
})();
