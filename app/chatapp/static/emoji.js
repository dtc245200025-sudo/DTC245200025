(() => {
  const choices = [
    ['😀','cuoi vui smile happy'], ['😂','cuoi haha laugh'], ['😊','cuoi vui smile'], ['🥰','yeu thuong love'], ['😍','yeu tim love'],
    ['❤️','tim yeu heart love'], ['💕','tim yeu heart'], ['👍','dong y tot like ok'], ['👏','vo tay gioi clap'], ['🙏','cam on thank please'],
    ['🎉','chuc mung party'], ['✨','sang dep sparkle'], ['🌸','hoa hong flower'], ['💗','tim hong heart'], ['🤗','om hug'],
    ['😎','ngau cool'], ['🤔','nghi think'], ['😢','buon khoc sad'], ['😭','khoc buon cry'], ['😅','cuoi ngai'], ['😴','ngu buon ngu sleep'],
    ['👋','chao hello bye'], ['👌','ok dong y'], ['🔥','lua hot'], ['💯','diem tot hundred'], ['☕','ca phe coffee'], ['🍀','may man lucky'], ['🐱','meo cat']
  ];
  const fold = value => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
  window.setupLinhEmoji = input => {
    const picker = document.querySelector('#chat-emoji-picker'), toggle = document.querySelector('#chat-emoji-toggle');
    const grid = document.querySelector('#chat-emoji-grid'), query = document.querySelector('#chat-emoji-query');
    const suggestions = document.querySelector('#chat-emoji-suggestions');
    let caret = input.value.length;
    const close = () => { picker.hidden = true; toggle.setAttribute('aria-expanded','false'); suggestions.hidden = true; };
    function insert(emoji, replaceToken = false) {
      if (input.disabled) return;
      const value = input.value, end = replaceToken ? input.selectionStart : caret;
      const token = replaceToken ? /:[\p{L}_-]{1,20}$/u.exec(value.slice(0,end)) : null;
      const start = token ? end - token[0].length : end;
      if (value.length - (end - start) + emoji.length > 1000) return;
      input.setRangeText(emoji, start, end, 'end');
      caret = input.selectionStart; input.focus(); input.dispatchEvent(new Event('input',{bubbles:true})); close();
    }
    function buttons(container, term, replaceToken) {
      container.replaceChildren();
      choices.filter(([emoji, words]) => !term || fold(words).includes(fold(term)) || emoji === term).slice(0,28).forEach(([emoji, words]) => {
        const button = document.createElement('button'); button.type = 'button'; button.textContent = emoji;
        button.title = words; button.setAttribute('aria-label', `Chèn ${emoji}`);
        button.addEventListener('mousedown', event => event.preventDefault());
        button.addEventListener('click', () => insert(emoji, replaceToken)); container.append(button);
      });
      if (!container.childElementCount) { const note = document.createElement('small'); note.textContent = 'Không có emoji phù hợp.'; container.append(note); }
    }
    toggle.addEventListener('click', () => { caret = input.selectionStart ?? input.value.length; picker.hidden = !picker.hidden; toggle.setAttribute('aria-expanded',String(!picker.hidden)); if (!picker.hidden) { query.value=''; buttons(grid,'',false); query.focus(); } });
    query.addEventListener('input', () => buttons(grid, query.value, false));
    input.addEventListener('input', () => {
      caret = input.selectionStart;
      const match = /:([\p{L}_-]{1,20})$/u.exec(input.value.slice(0,caret));
      suggestions.hidden = !match;
      if (match) buttons(suggestions, match[1], true);
    });
    document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
    document.addEventListener('click', event => { if (!picker.contains(event.target) && !toggle.contains(event.target) && !suggestions.contains(event.target) && event.target !== input) close(); });
  };
})();
