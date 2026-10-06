/* Окно «Оставить заявку»: выбор WhatsApp / MAX / Telegram / звонок. Данные посетителя не собираются и не хранятся:
   в WhatsApp сообщение подставляется в ссылку, в MAX и Telegram текст копируется в буфер обмена для вставки в чат. */
(function () {
  var dlg = document.getElementById('lead-dialog');
  var buttons = [].slice.call(document.querySelectorAll('.js-lead'));
  if (!buttons.length) return;
  if (!dlg || typeof dlg.showModal !== 'function') {            // старый браузер: ведём на страницу контактов
    buttons.forEach(function (b) { b.addEventListener('click', function () { location.href = '/kontakty/'; }); });
    return;
  }
  var what = document.getElementById('lead-what');
  var copied = document.getElementById('lead-copied');
  var wa = dlg.querySelector('.cta-wa'), tg = dlg.querySelector('.cta-tg'), mx = dlg.querySelector('.cta-max');
  var text = '';

  function message(title) {
    return 'Здравствуйте! Интересует: ' + title + '. Страница: ' + location.href.split('#')[0] + ' Подскажите цену, наличие и условия монтажа.';
  }
  function copy(t) {
    if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(t).then(function () { copied.hidden = false; }, function () { copied.hidden = true; }); }
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      var title = b.getAttribute('data-lead') || document.title;
      text = message(title);
      what.textContent = title;
      copied.hidden = true;
      if (wa) wa.href = 'https://wa.me/' + dlg.dataset.wa + '?text=' + encodeURIComponent(text);
      dlg.showModal();
      var first = dlg.querySelector('.cta-btn'); if (first) first.focus();
      if (window.ym) { try { ym(parseInt((document.querySelector('script[src*="mc.yandex.ru"]') || {}).src.split('id=')[1], 10), 'reachGoal', 'lead_open'); } catch (e) { /* счётчик необязателен */ } }
    });
  });
  [tg, mx].forEach(function (a) { if (a) a.addEventListener('click', function () { copy(text); }); });
  dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });       // клик по затемнению
})();
