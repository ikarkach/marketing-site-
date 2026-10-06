/* Шапка и меню: мега-меню «Каталог» (3 колонки), простые выпадающие списки, бургер на телефонах. Без библиотек.
   Десктоп: клик или наведение (с задержкой ~150 мс) открывает «Каталог»; в левой колонке категория выбирается наведением/кликом;
   Esc и клик вне меню закрывают; стрелки, Tab и Enter работают. Телефон (<1024 px): полноэкранное меню, вложенность «гармошкой». */
(function () {
  var header = document.getElementById('site-header');
  if (!header) return;
  var nav = header.querySelector('.site-nav');
  var burger = header.querySelector('.nav-burger');
  var items = [].slice.call(header.querySelectorAll('.nav-item--mega, .nav-item--sub'));
  var desktop = window.matchMedia('(min-width: 1024px)');
  var canHover = window.matchMedia('(hover: hover)');
  var timers = new WeakMap();
  var HOVER_DELAY = 150;

  function toggleOf(item) { return item.querySelector(':scope > .nav-toggle'); }
  function setOpen(item, open) {
    item.classList.toggle('is-open', open);
    var t = toggleOf(item);
    if (t) t.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  function closeAll(except) { items.forEach(function (it) { if (it !== except) setOpen(it, false); }); }
  function hoverMode() { return desktop.matches && canHover.matches; }
  function links(root) { return [].slice.call(root.querySelectorAll('a[href], button:not([disabled])')).filter(function (e) { return e.offsetParent !== null; }); }

  items.forEach(function (item) {
    var btn = toggleOf(item);

    btn.addEventListener('click', function (e) {
      // мышь на компьютере: наведение уже открыло список, клик закрепляет его; клавиатура и телефон: переключатель
      if (hoverMode() && e.detail > 0 && item.classList.contains('is-open')) return;
      var open = !item.classList.contains('is-open');
      if (desktop.matches) closeAll(item);
      setOpen(item, open);
    });

    item.addEventListener('mouseenter', function () {
      if (!hoverMode()) return;
      clearTimeout(timers.get(item));
      timers.set(item, setTimeout(function () { closeAll(item); setOpen(item, true); }, HOVER_DELAY));
    });
    item.addEventListener('mouseleave', function () {
      if (!hoverMode()) return;
      clearTimeout(timers.get(item));
      timers.set(item, setTimeout(function () { setOpen(item, false); }, HOVER_DELAY));
    });
    item.addEventListener('focusout', function (e) {
      if (desktop.matches && e.relatedTarget && !item.contains(e.relatedTarget)) setOpen(item, false);
    });

    btn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' && desktop.matches) {
        e.preventDefault(); closeAll(item); setOpen(item, true);
        var first = item.querySelector('.mega__cat-btn, .nav-panel a');
        if (first) first.focus();
      }
    });
  });

  // стрелки между пунктами верхнего уровня
  [].slice.call(header.querySelectorAll('.nav-link, .nav-toggle')).forEach(function (el) {
    el.addEventListener('keydown', function (e) {
      if (!desktop.matches || (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft')) return;
      var all = [].slice.call(header.querySelectorAll('.nav-link, .nav-toggle'));
      var i = all.indexOf(el) + (e.key === 'ArrowRight' ? 1 : -1);
      if (all[i]) { e.preventDefault(); all[i].focus(); }
    });
  });

  // мега-меню: выбор категории в левой колонке
  [].slice.call(header.querySelectorAll('.mega')).forEach(function (mega) {
    var cats = [].slice.call(mega.querySelectorAll('.mega__cat'));
    function activate(cat) {
      cats.forEach(function (c) {
        var on = c === cat;
        c.classList.toggle('is-active', on);
        c.querySelector('.mega__cat-btn').setAttribute('aria-expanded', on ? 'true' : 'false');
      });
    }
    cats.forEach(function (cat, idx) {
      var b = cat.querySelector('.mega__cat-btn');
      b.addEventListener('mouseenter', function () { if (hoverMode()) activate(cat); });
      b.addEventListener('focus', function () { if (desktop.matches) activate(cat); });
      b.addEventListener('click', function () {
        if (desktop.matches) { activate(cat); return; }
        var open = !cat.classList.contains('is-open');          // телефон: «гармошка»
        cats.forEach(function (c) { c.classList.remove('is-open'); c.querySelector('.mega__cat-btn').setAttribute('aria-expanded', 'false'); });
        cat.classList.toggle('is-open', open);
        b.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
      b.addEventListener('keydown', function (e) {
        if (!desktop.matches) return;
        if (e.key === 'ArrowDown' && cats[idx + 1]) { e.preventDefault(); cats[idx + 1].querySelector('.mega__cat-btn').focus(); }
        else if (e.key === 'ArrowUp' && cats[idx - 1]) { e.preventDefault(); cats[idx - 1].querySelector('.mega__cat-btn').focus(); }
        else if (e.key === 'ArrowRight') { var l = links(cat.querySelector('.mega__sub')); if (l[0]) { e.preventDefault(); l[0].focus(); } }
        else if (e.key === 'Home') { e.preventDefault(); cats[0].querySelector('.mega__cat-btn').focus(); }
        else if (e.key === 'End') { e.preventDefault(); cats[cats.length - 1].querySelector('.mega__cat-btn').focus(); }
      });
      cat.querySelector('.mega__sub').addEventListener('keydown', function (e) {
        if (!desktop.matches) return;
        var l = links(cat.querySelector('.mega__sub')); var i = l.indexOf(document.activeElement);
        if (e.key === 'ArrowDown' && i < l.length - 1) { e.preventDefault(); l[i + 1].focus(); }
        else if (e.key === 'ArrowUp' && i > 0) { e.preventDefault(); l[i - 1].focus(); }
        else if (e.key === 'ArrowLeft') { e.preventDefault(); b.focus(); }
      });
    });
    // третий уровень: стрелка раскрывает список
    [].slice.call(mega.querySelectorAll('.mega__chev')).forEach(function (chev) {
      chev.addEventListener('click', function () {
        var li = chev.closest('.mega__item'); var open = !li.classList.contains('is-open');
        li.classList.toggle('is-open', open); chev.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
  });

  // бургер (телефон)
  function setMenu(open) {
    nav.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    document.body.style.overflow = open && !desktop.matches ? 'hidden' : '';
  }
  if (burger) burger.addEventListener('click', function () { setMenu(!nav.classList.contains('is-open')); });

  document.addEventListener('click', function (e) { if (desktop.matches && !header.contains(e.target)) closeAll(); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var open = items.filter(function (it) { return it.classList.contains('is-open'); });
    closeAll();
    if (open[0] && header.contains(document.activeElement)) { var t = toggleOf(open[0]); if (t) t.focus(); }
    if (burger && nav.classList.contains('is-open') && !desktop.matches) { setMenu(false); burger.focus(); }
  });
  // ссылка внутри мобильного меню: закрыть меню
  nav.addEventListener('click', function (e) { if (!desktop.matches && e.target.closest('a')) setMenu(false); });
  // кнопка «Рассчитать стоимость» / «Оставить заявку» из меню: закрыть меню, окно откроет lead.js
  header.addEventListener('click', function (e) { if (e.target.closest('.js-lead')) { closeAll(); if (!desktop.matches) setMenu(false); } });

  var onChange = function () { closeAll(); setMenu(false); };
  if (desktop.addEventListener) desktop.addEventListener('change', onChange);
})();
