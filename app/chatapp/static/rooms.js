(() => {
  const visibility = document.querySelector('#room-visibility');
  const mode = document.querySelector('#room-join-mode');
  function updateFields() {
    if (!visibility || !mode) return;
    const isPublic = visibility.value === 'public';
    const password = !isPublic && mode.value === 'password';
    document.querySelector('#room-public-fields').hidden = !isPublic;
    document.querySelector('[name="max_members"]').disabled = !isPublic;
    document.querySelector('#room-private-fields').hidden = isPublic;
    mode.disabled = isPublic;
    document.querySelector('#room-password-label').hidden = !password;
    const field = document.querySelector('[name="room_password"]');
    field.disabled = !password;
    field.required = password;
    document.querySelector('#room-mode-description').textContent = {
      approval: 'Mọi người có thể tìm phòng và gửi yêu cầu; chỉ vào được sau khi bạn phê duyệt.',
      password: 'Mọi người có thể tìm phòng nhưng phải nhập đúng mật khẩu để xem và gửi tin nhắn.',
      invite: 'Phòng không hiện trong tìm kiếm của người chưa tham gia. Tạo link mời trong trang Quản lý sau khi tạo phòng.'
    }[mode.value] || '';
  }
  visibility?.addEventListener('change', updateFields);
  mode?.addEventListener('change', updateFields);
  updateFields();
  document.querySelector('[data-copy-invitation]')?.addEventListener('click', async () => {
    const field = document.querySelector('#invitation-url');
    const status = document.querySelector('#invitation-copy-status');
    try { await navigator.clipboard.writeText(field.value); status.textContent = 'Đã sao chép link mời.'; }
    catch { field.focus(); field.select(); status.textContent = 'Link đã được chọn. Nhấn Ctrl+C để sao chép.'; }
  });
  const waiting = document.querySelector('[data-wait-room-id]');
  const managing = document.querySelector('[data-manage-room-id]');
  window.linhSocket?.on('room_request_result', data => {
    if (waiting && Number(waiting.dataset.waitRoomId) === data.room_id) window.location.reload();
  });
  window.linhSocket?.on('room_request_pending', data => {
    if (managing && Number(managing.dataset.manageRoomId) === data.room_id) window.location.reload();
  });
})();
