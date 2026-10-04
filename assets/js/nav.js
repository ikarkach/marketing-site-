/* Главное меню: выпадающие списки (наведение, клик, клавиатура) и бургер на телефонах. Без библиотек. */
(function () {
  var nav = document.querySelector('.site-nav');
  if (!nav) return;
  var burger = nav.querySelector('.nav-burger');
  var list = nav.querySelector('.nav-list');
  var items = [].slice.call(nav.querySelectorAll('.nav-item--sub'));
  var desktop = window.matchMedia('(min-width: 769px)');
  var canHover = window.matchMedia('(hover: hover)');
  var timers = new WeakMap();

  function toggleOf(item) { return item.querySelector('.nav-toggle'); }
  function panelLinks(item) { return [].slice.call(item.querySelectorAll('.nav-panel a')); }
  function setOpen(item, open) {
    item.classList.toggle('is-open', open);
    toggleOf(item).setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  function closeAll(except) {
    items.forEach(function (it) { if (it !== except) setOpen(it, false); });
  }
  function hoverMode() { return desktop.matches && canHover.matches; }

  items.forEach(function (item, idx) {
    var btn = toggleOf(item);

    btn.addEventListener('click', function (e) {
      // мышь на компьютере: список уже открыт наведением, клик его не закрывает; клавиатура и телефон: переключение
      if (hoverMode() && e.detail > 0) { closeAll(item); setOpen(item, true); return; }
      var open = !item.classList.contains('is-open');
      if (desktop.matches) closeAll(item);
      setOpen(item, open);
    });

    item.addEventListener('mouseenter', function () {
      if (!hoverMode()) return;
      clearTimeout(timers.get(item));
      closeAll(item);
      setOpen(item, true);
    });
    item.addEventListener('mouseleave', function () {
      if (!hoverMode()) return;
      timers.set(item, setTimeout(function () { setOpen(item, false); }, 180));
    });

    // фокус ушёл на другой элемент вне пункта: закрыть
    item.addEventListener('focusout', function (e) {
      if (e.relatedTarget && !item.contains(e.relatedTarget)) setOpen(item, false);
    });

    btn.addEventListener('keydown', function (e) {
      var links = panelLinks(item);
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        closeAll(item); setOpen(item, true);
        if (links[0]) links[0].focus();
      } else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        var all = [].slice.call(nav.querySelectorAll('.nav-toggle, .nav-link'));
        var i = all.indexOf(btn) + (e.key === 'ArrowRight' ? 1 : -1);
        if (desktop.matches && all[i]) { e.preventDefault(); all[i].focus(); }
      }
    });

    item.querySelector('.nav-panel').addEventListener('keydown', function (e) {
      var links = panelLinks(item);
      var i = links.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' && i < links.length - 1) { e.preventDefault(); links[i + 1].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); if (i > 0) links[i - 1].focus(); else btn.focus(); }
      else if (e.key === 'Escape') { e.preventDefault(); setOpen(item, false); btn.focus(); }
    });
  });

  // стрелки между простыми ссылками верхнего уровня
  [].slice.call(nav.querySelectorAll('.nav-link')).forEach(function (a) {
    a.addEventListener('keydown', function (e) {
      if (!desktop.matches) return;
      var all = [].slice.call(nav.querySelectorAll('.nav-toggle, .nav-link'));
      var i = all.indexOf(a) + (e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0);
      if ((e.key === 'ArrowRight' || e.key === 'ArrowLeft') && all[i]) { e.preventDefault(); all[i].focus(); }
    });
  });

  // бургер (телефон)
  if (burger) {
    burger.addEventListener('click', function () {
      var open = !list.classList.contains('is-open');
      list.classList.toggle('is-open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // клик вне меню и Esc закрывают списки
  document.addEventListener('click', function (e) { if (!nav.contains(e.target)) closeAll(); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var open = items.filter(function (it) { return it.classList.contains('is-open'); });
    closeAll();
    if (open[0] && nav.contains(document.activeElement)) toggleOf(open[0]).focus();
    if (burger && list.classList.contains('is-open') && !desktop.matches) {
      list.classList.remove('is-open'); burger.setAttribute('aria-expanded', 'false'); burger.focus();
    }
  });

  // переход между десктопом и телефоном: сбросить состояние
  desktop.addEventListener && desktop.addEventListener('change', function () {
    closeAll();
    if (list) list.classList.remove('is-open');
    if (burger) burger.setAttribute('aria-expanded', 'false');
  });
})();
