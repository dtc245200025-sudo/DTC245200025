(() => {
  const root = document.querySelector('[data-conversation]');
  if (!root) return;
  const scope = root.dataset.scope, targetId = Number(root.dataset.targetId), me = Number(root.dataset.currentUser);
  const base = `/chat/${scope}/${targetId}`, socket = window.linhSocket;
  const messages = root.querySelector('.direct-messages'), input = document.querySelector('#chat-message-input');
  const status = document.querySelector('#chat-connection-status'), send = document.querySelector('#chat-send');
  const fileInput = document.querySelector('#chat-file'), filePicker = document.querySelector('#chat-file-picker');
  const older = document.querySelector('#chat-load-older'), csrf = document.querySelector('#chat-search-form [name="csrf_token"]').value;
  const typing = window.createLinhTyping({scope, targetId, input, indicator: document.querySelector('#chat-typing'), currentUser: me});
  window.setupLinhEmoji(input);
  const stored = new Map(), stateCache = new Map();
  const queues = {delivered: new Set(), seen: new Set()}, acknowledged = {delivered: new Set(), seen: new Set()};
  let allowed = root.dataset.canSend === 'true', busy = false, pending = null, selectedFile = null;
  let syncedThrough = 0, syncing = false, syncAgain = false, ackTimer, ackBusy = false;
  const matches = data => data.scope === scope && data.target_id === targetId;
  const date = raw => raw ? new Date(/[Zz]|[+-]\d\d:\d\d$/.test(raw) ? raw : `${raw}Z`).toLocaleString('vi-VN') : 'Chưa có';
  function controls() { input.disabled = !allowed; send.disabled = busy || !allowed; filePicker.disabled = busy || !allowed; document.querySelector('#chat-file-remove').disabled = busy; document.querySelector('#chat-emoji-toggle').disabled = !allowed; document.querySelector('#chat-read-only').hidden = allowed; if (!allowed) { typing.stop(); typing.clear(); } }
  async function api(path, options = {}) {
    const response = await fetch(path, {cache: 'no-store', ...options});
    if (response.redirected) { window.location.assign('/login'); throw new Error('Phiên đăng nhập đã hết hạn.'); }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `Yêu cầu chưa thành công (${response.status}).`);
    return data;
  }
  const post = (path, values) => api(path, {method: 'POST', body: new URLSearchParams({...values, csrf_token: csrf})});
  function mergeState(id, incoming) {
    const old = stateCache.get(id) || {recipients:0, delivered:0, seen:0};
    const value = {recipients: Math.max(old.recipients, incoming.recipients), delivered: Math.max(old.delivered, incoming.delivered), seen: Math.max(old.seen, incoming.seen)};
    stateCache.set(id, value);
    const data = stored.get(id), element = messages.querySelector(`[data-message-id="${id}"] .message-state`);
    if (!element || !data || data.user_id !== me) return;
    if (!data.receipts_tracked) { element.textContent = 'Lịch sử cũ'; return; }
    const suffix = amount => value.recipients > 1 ? ` ${amount}/${value.recipients}` : '';
    element.textContent = value.seen ? `Đã xem${suffix(value.seen)}` : value.delivered ? `Đã nhận${suffix(value.delivered)}` : 'Đã gửi';
  }
  function eligible(data) { return data?.receipts_tracked && data.user_id !== me && data.recipient_ids.includes(me); }
  function enqueue(kind, id) {
    if (acknowledged[kind].has(id)) return;
    queues[kind].add(id); clearTimeout(ackTimer); ackTimer = setTimeout(flushAcks, 100);
  }
  async function flushAcks() {
    if (!socket.connected || ackBusy) return;
    ackBusy = true;
    try {
      for (const kind of ['delivered','seen']) {
        while (socket.connected && queues[kind].size) {
          const ids = [...queues[kind]].slice(0,100);
          const result = await new Promise(resolve => socket.timeout(5000).emit('message_receipt', {scope, target_id: targetId, message_ids: ids, kind}, (error, value) => resolve(error ? null : value)));
          if (!result) return;
          ids.forEach(id => { queues[kind].delete(id); if (result.ok) acknowledged[kind].add(id); });
          if (!result.ok) { status.textContent = 'Chưa ghi được xác nhận nhận/xem. Bạn có thể tải lại trang.'; return; }
        }
      }
    } finally { ackBusy = false; if (socket.connected && (queues.delivered.size || queues.seen.size)) { clearTimeout(ackTimer); ackTimer = setTimeout(flushAcks, 500); } }
  }
  function checkSeen() {
    if (document.hidden || !document.hasFocus() || document.querySelector('#chat-message-details').open) return;
    const box = messages.getBoundingClientRect();
    messages.querySelectorAll('[data-message-id]').forEach(element => {
      const data = stored.get(Number(element.dataset.messageId));
      if (!eligible(data)) return;
      const bounds = element.getBoundingClientRect();
      const visible = Math.min(bounds.bottom, box.bottom, innerHeight) - Math.max(bounds.top, box.top, 0);
      if (visible >= Math.min(bounds.height * .6, 120)) enqueue('seen', data.id);
    });
  }
  const observer = new IntersectionObserver(checkSeen, {root: messages, threshold: [.1,.6,1]});
  function hydrate(data, element) {
    stored.set(data.id, data);
    element.querySelectorAll('time').forEach(time => { time.textContent = date(time.dateTime); });
    mergeState(data.id, data.receipt_summary);
    if (eligible(data)) enqueue('delivered', data.id);
    observer.observe(element);
  }
  function render(data, scroll = true) {
    if (!matches(data)) return;
    const existing = messages.querySelector(`[data-message-id="${Number(data.id)}"]`);
    if (existing) { mergeState(data.id, data.receipt_summary); return; }
    const nearBottom = messages.scrollHeight - messages.scrollTop - messages.clientHeight < 90;
    document.querySelector('#chat-empty')?.remove();
    const element = document.createElement('article'); element.className = `direct-message${data.user_id === me ? ' is-mine' : ''}`;
    element.dataset.messageId = String(data.id); element.tabIndex = 0; element.setAttribute('aria-label',`Tin nhắn ${data.id}. Nhấn Enter để xem thời gian`);
    const bubble = document.createElement('div'); bubble.className = 'direct-bubble';
    const author = document.createElement('a'); author.className = 'direct-author'; author.href = `/users/${Number(data.user_id)}`; author.textContent = data.username; bubble.append(author);
    if (data.content) { const text = document.createElement('p'); text.textContent = data.content; bubble.append(text); }
    if (data.attachment) {
      const attachment = data.attachment, wrapper = document.createElement('div'); wrapper.className = 'message-attachment';
      if (attachment.is_image) { const image = document.createElement('img'); image.src = attachment.preview_url; image.alt = `Ảnh đính kèm ${attachment.filename}`; image.loading = 'lazy'; if (scroll && nearBottom) image.addEventListener('load', () => { messages.scrollTop = messages.scrollHeight; }); wrapper.append(image); }
      const link = document.createElement('a'); link.href = attachment.download_url; link.textContent = `Tải xuống ${attachment.filename}`; link.className = 'attachment-download';
      const size = document.createElement('small'); size.textContent = `${(attachment.size / 1024).toFixed(1)} KB`; wrapper.append(link,size); bubble.append(wrapper);
    }
    const meta = document.createElement('div'); meta.className = 'message-meta';
    const time = document.createElement('time'); time.dateTime = data.created_at;
    const state = document.createElement('span'); state.className = 'message-state';
    const details = document.createElement('button'); details.type = 'button'; details.className = 'message-details-button'; details.textContent = 'ⓘ'; details.setAttribute('aria-label',`Chi tiết tin nhắn ${data.id}`);
    meta.append(time,state,details); bubble.append(meta); element.append(bubble);
    const next = [...messages.querySelectorAll('[data-message-id]')].find(node => Number(node.dataset.messageId) > data.id);
    messages.insertBefore(element,next || null); hydrate(data,element);
    if (scroll && (nearBottom || data.user_id === me)) messages.scrollTop = messages.scrollHeight;
    checkSeen();
  }
  async function refreshStates() {
    const ids = [...stored.values()].filter(item => item.user_id === me).map(item => item.id);
    for (let index=0; index<ids.length; index+=100) {
      const body = new URLSearchParams({csrf_token:csrf}); ids.slice(index,index+100).forEach(id => body.append('message_ids',String(id)));
      const data = await api(`${base}/states`, {method:'POST',body}); data.states.forEach(item => mergeState(item.id,item.summary));
    }
  }
  async function sync() {
    if (syncing) { syncAgain = true; return; } syncing = true;
    try {
      let more = true, count=0;
      do { const data = await api(`${base}/history?after=${syncedThrough}`); allowed = data.can_send; controls(); data.messages.forEach(item => render(item)); if (data.messages.length) syncedThrough = Math.max(syncedThrough,...data.messages.map(item => item.id)); more=data.has_more; count++; } while (more && count<20);
      if (more) status.textContent = 'Còn tin chưa đồng bộ. Tải lại trang để xem bản mới nhất.';
      await refreshStates(); checkSeen(); flushAcks();
    } catch (error) { status.textContent = error.message; }
    finally { syncing=false; if (syncAgain) { syncAgain=false; sync(); } }
  }
  const socketTarget = () => ({[scope === 'room' ? 'room_id' : 'conversation_id']:targetId});
  function join() { socket.emit(scope === 'room' ? 'join' : 'direct_join',socketTarget(), result => { status.textContent = result?.ok ? 'Đã kết nối · Tin nhắn được lưu trong PostgreSQL' : result?.error || 'Chưa được phép kết nối.'; if (result?.ok) sync(); }); }
  socket.on('connect',join); socket.on('disconnect',() => { status.textContent='Mất kết nối, đang thử lại…'; });
  socket.on('connect_error',() => { status.textContent='Chưa kết nối được. Kiểm tra mạng hoặc đăng nhập lại.'; });
  socket.on(scope === 'room' ? 'new_message' : 'direct_message',data => render(data));
  socket.on('receipt_updated', data => { if (matches(data)) mergeState(data.message_id,data.summary); });
  socket.on('direct_changed',data => { if (scope === 'direct' && data.conversation_id === targetId) sync(); });
  socket.on('friends_changed',() => { if (scope === 'direct') sync(); });
  socket.on('room_left',data => { if (scope === 'room' && data.room_id === targetId) window.location.assign('/rooms/search'); });
  older.addEventListener('click',async () => { older.disabled=true; try { const first=messages.querySelector('[data-message-id]'), height=messages.scrollHeight; const data=await api(`${base}/history?before=${first ? Number(first.dataset.messageId) : 0}`); data.messages.forEach(item => render(item,false)); messages.scrollTop += messages.scrollHeight-height; older.hidden=!data.has_more; checkSeen(); } catch(error) { status.textContent=error.message; } finally { older.disabled=false; } });
  function chooseFile(file) {
    if (file && (file.size === 0 || file.size>10*1024*1024)) { status.textContent='Chọn tệp không rỗng, tối đa 10 MB.'; fileInput.value=''; return; }
    selectedFile=file; document.querySelector('#chat-pending-file').hidden=!file;
    document.querySelector('#chat-file-name').textContent=file ? `${file.name} · ${(file.size/1024).toFixed(1)} KB` : '';
    if (!file) fileInput.value='';
  }
  filePicker.addEventListener('click',() => fileInput.click()); fileInput.addEventListener('change',() => chooseFile(fileInput.files[0] || null)); document.querySelector('#chat-file-remove').addEventListener('click',() => chooseFile(null));
  document.querySelector('#chat-message-form').addEventListener('submit',async event => {
    event.preventDefault(); const content=input.value.trim(), file=selectedFile;
    if ((!content && !file) || !allowed || busy) return;
    if (!socket.connected) { status.textContent='Chưa có kết nối, chưa gửi tin nhắn.'; return; }
    typing.stop();
    if (!pending || pending.content!==content || pending.file!==file) pending={content,file,nonce:[...crypto.getRandomValues(new Uint8Array(16))].map(value => value.toString(16).padStart(2,'0')).join('')};
    busy=true; controls();
    try {
      let result;
      if (file) {
        const body=new FormData(); body.append('file',file); body.append('content',content); body.append('client_nonce',pending.nonce); body.append('csrf_token',csrf);
        const controller=new AbortController(), timer=setTimeout(() => controller.abort(),60000);
        try { result=await api(`${base}/attachments`,{method:'POST',body,signal:controller.signal}); } finally { clearTimeout(timer); }
      } else {
        result=await new Promise((resolve,reject) => socket.timeout(6000).emit(scope==='room' ? 'send_message' : 'direct_send',{...socketTarget(),content,client_nonce:pending.nonce},(error,value) => error ? reject(new Error('Chưa có xác nhận. Gửi lại cùng nội dung sẽ không tạo tin trùng.')) : resolve(value)));
      }
      if (!result?.ok) throw new Error(result?.error || 'Chưa gửi được. Hãy thử lại.');
      render(result.message); if (input.value.trim()===content) input.value=''; if (selectedFile===file) chooseFile(null); pending=null;
      status.textContent='Đã gửi · Đã lưu trên máy chủ'; input.focus();
    } catch(error) { status.textContent=error.name==='AbortError' ? 'Chưa xác nhận được tệp. Gửi lại cùng tệp sẽ không tạo tin trùng.' : error.message; sync(); }
    finally { busy=false; controls(); }
  });
  let searchVersion=0;
  const results=document.querySelector('#chat-search-results'), searchClose=document.querySelector('#chat-search-close');
  searchClose.addEventListener('click',() => { searchVersion++; results.hidden=true; searchClose.hidden=true; });
  document.querySelector('#chat-search-form').addEventListener('submit',async event => {
    event.preventDefault(); const version=++searchVersion, q=document.querySelector('#chat-search-input').value.trim();
    try { const data=await post(`${base}/search`,{q}); if (version!==searchVersion) return; results.replaceChildren();
      const note=document.createElement('p'); note.textContent=`${data.messages.length} kết quả (tối đa 50)`; results.append(note);
      data.messages.forEach(item => { const button=document.createElement('button'); button.type='button'; button.className='secondary chat-search-hit'; button.textContent=`${item.username}: ${item.content || item.attachment?.filename || ''} · ${date(item.created_at)}`; button.addEventListener('click',() => { render(item,false); const element=messages.querySelector(`[data-message-id="${item.id}"]`); element.scrollIntoView({block:'center'}); element.classList.add('message-highlight'); setTimeout(() => element.classList.remove('message-highlight'),2000); checkSeen(); }); results.append(button); }); results.hidden=false; searchClose.hidden=false;
    } catch(error) { status.textContent=error.message; }
  });
  const dialog=document.querySelector('#chat-message-details'), detailsBody=document.querySelector('#chat-details-body');
  let detailVersion=0;
  async function details(id) {
    const version=++detailVersion; detailsBody.textContent='Đang tải…'; if (!dialog.open) dialog.showModal();
    try { const data=await api(`${base}/messages/${id}/details`); if (version!==detailVersion) return; detailsBody.replaceChildren();
      const sent=document.createElement('p'); sent.textContent=`Đã gửi: ${date(data.sent_at)}`; detailsBody.append(sent);
      if (!data.tracked) { const note=document.createElement('p'); note.textContent='Tin lịch sử cũ: chưa ghi nhận xác nhận nhận/xem, không tạo thời gian giả.'; detailsBody.append(note); }
      else if (!data.receipts.length) { const note=document.createElement('p'); note.textContent='Không có xác nhận dành cho bạn ở tin nhắn này.'; detailsBody.append(note); }
      else { if (!data.author) { const note=document.createElement('p'); note.textContent='Chỉ hiển thị xác nhận của bạn.'; detailsBody.append(note); }
        data.receipts.forEach(item => { const section=document.createElement('section'); section.className='detail-receipt'; const title=document.createElement('strong'); title.textContent=item.name; const received=document.createElement('p'); received.textContent=`Đã nhận: ${date(item.delivered_at)}`; const seen=document.createElement('p'); seen.textContent=`Đã xem: ${date(item.seen_at)}`; section.append(title,received,seen); detailsBody.append(section); }); }
    } catch(error) { if (version===detailVersion) detailsBody.textContent=error.message; }
  }
  document.querySelector('#chat-details-close').addEventListener('click',() => dialog.close());
  dialog.addEventListener('close',checkSeen);
  messages.addEventListener('click',event => { const element=event.target.closest('[data-message-id]'); if (!element || event.target.closest('a') || window.getSelection().toString()) return; details(Number(element.dataset.messageId)); });
  messages.addEventListener('keydown',event => { if (event.key==='Enter' && event.target.matches('[data-message-id]')) { event.preventDefault(); details(Number(event.target.dataset.messageId)); } });
  messages.addEventListener('scroll',checkSeen,{passive:true}); document.addEventListener('visibilitychange',checkSeen); window.addEventListener('focus',checkSeen); input.addEventListener('focus',checkSeen);
  messages.querySelectorAll('[data-message-id]').forEach(element => { const data=JSON.parse(element.dataset.message); syncedThrough=Math.max(syncedThrough,data.id); hydrate(data,element); });
  messages.scrollTop=messages.scrollHeight; controls(); if (socket.connected) join();
  window.addEventListener('pagehide',() => { typing.stop(); socket.emit(scope==='room' ? 'leave' : 'direct_leave',socketTarget()); });
})();
