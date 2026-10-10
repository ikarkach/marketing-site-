/* Кнопка «Скопировать ссылку» на странице модели: копирует постоянный адрес страницы (data-url) в буфер обмена.
   Если буфер недоступен (старый браузер, http), выделяет адрес для ручного копирования через prompt. */
(function () {
  var buttons = [].slice.call(document.querySelectorAll('.js-copy-link'));
  if (!buttons.length) return;
  var note = document.querySelector('.copy-note');
  var timer;
  function done(ok, url) {
    if (!note) return;
    note.textContent = ok ? 'Ссылка скопирована' : 'Скопируйте ссылку: ' + url;
    note.hidden = false;
    clearTimeout(timer);
    timer = setTimeout(function () { note.hidden = true; }, 4000);
  }
  function legacy(url) {
    var ta = document.createElement('textarea');
    ta.value = url; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      var url = b.getAttribute('data-url') || location.href.split('#')[0];
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () { done(true, url); }, function () { done(legacy(url), url); });
      } else {
        done(legacy(url), url);
      }
    });
  });
})();