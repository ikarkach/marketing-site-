/* Каталог: фильтры (с живыми счётчиками), «таблетки» типов, сортировка, вид «плитка/список», панель фильтров на телефоне.
   Состояние пишется в адрес страницы (?brand=hisense&inverter=1&type=wall...), поэтому ссылкой можно поделиться.
   Все карточки есть в HTML, поэтому ссылки видны поисковикам. Без библиотек. */
(function () {
  var grid = document.getElementById('catalog-grid');
  var form = document.getElementById('catalog-filters');
  if (!grid || !form) return;
  var cards = [].slice.call(grid.children);
  var chips = [].slice.call(document.querySelectorAll('.chip[data-type]'));
  var countEl = document.getElementById('catalog-count');
  var emptyEl = document.getElementById('catalog-empty');
  var sortSel = document.getElementById('catalog-sort');
  var dirBtn = document.getElementById('catalog-dir');
  var panel = document.getElementById('catalog-filters-panel');
  var overlay = document.getElementById('catalog-overlay');
  var openBtn = document.getElementById('catalog-filters-open');
  var closeBtn = document.getElementById('catalog-filters-close');
  var applyBtn = document.getElementById('catalog-filters-apply');
  var applyCount = document.getElementById('catalog-apply-count');
  var badge = document.getElementById('catalog-filters-count');
  var viewBtns = [].slice.call(document.querySelectorAll('.view-toggle__btn'));
  var state = { type: '', view: 'tiles' };
  var EFF = { a3: 'A+++', a2: 'A++', a1: 'A+', a0: 'A' };
  var mobile = window.matchMedia('(max-width: 1023px)');

  function num(v) { var n = parseFloat(v); return isNaN(n) ? null : n; }
  function inputs(name) { return [].slice.call(form.querySelectorAll('input[name="' + name + '"]')); }
  function checked(name) { return inputs(name).filter(function (i) { return i.checked; }).map(function (i) { return i.value; }); }
  function range(i) { return [num(i.dataset.min), num(i.dataset.max)]; }
  function overlap(lo, hi, r) { return lo !== null && hi !== null && hi >= r[0] && lo <= r[1]; }

  function collect() {
    var noise = form.querySelector('input[name="noise"]:checked');
    return {
      brand: checked('brand'), series: checked('series'), inverter: checked('inverter'), hp: checked('hp'), eff: checked('eff'),
      kw: inputs('kw').filter(function (i) { return i.checked; }).map(range),
      pmin: num(form.elements.pmin.value), pmax: num(form.elements.pmax.value),
      noise: noise && noise.value ? num(noise.value) : null
    };
  }

  // подходит ли карточка варианту val из группы name
  function optMatch(name, c, val) {
    var d = c.dataset;
    switch (name) {
      case 'brand': return d.brand === val;
      case 'series': return d.id === val;
      case 'inverter': return val === '1' ? (d.tech === 'yes' || d.tech === 'both') : (d.tech === 'no' || d.tech === 'both');
      case 'hp': return d.hp !== '' && (val === '1') === (d.hp === 'yes');
      case 'eff': return (d.eff || '').split(' ').indexOf(EFF[val]) >= 0;
      case 'kw': return overlap(num(d.kwMin), num(d.kwMax), val);
      case 'noise': var n = num(d.noise); return n !== null && n <= parseFloat(val);
    }
    return true;
  }

  // подходит ли карточка под все условия; skip — группа, которую не учитываем (для счётчиков)
  function matches(c, f, skip) {
    var d = c.dataset;
    if (state.type && d.type !== state.type) return false;
    var groups = ['brand', 'series', 'inverter', 'hp', 'eff', 'kw'];
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i], vals = f[g];
      if (g === skip || !vals.length) continue;
      if (!vals.some(function (v) { return optMatch(g, c, v); })) return false;
    }
    if (skip !== 'price' && (f.pmin !== null || f.pmax !== null)) {
      var lo = num(d.priceMin), hi = num(d.priceMax);
      if (lo === null) return false;
      if (f.pmin !== null && hi < f.pmin) return false;
      if (f.pmax !== null && lo > f.pmax) return false;
    }
    if (skip !== 'noise' && f.noise !== null && !optMatch('noise', c, f.noise)) return false;
    return true;
  }

  // счётчики у вариантов: сколько серий останется, если выбрать этот вариант (остальные группы учитываются)
  function updateCounts(f) {
    [].slice.call(form.querySelectorAll('.filter-group')).forEach(function (grp) {
      var name = grp.dataset.group;
      if (name === 'price') return;
      var anyVisible = false;
      [].slice.call(grp.querySelectorAll('.filter-opt')).forEach(function (opt) {
        var inp = opt.querySelector('input'); var out = opt.querySelector('.filter-opt__n');
        if (!out) { anyVisible = true; return; }
        var val = name === 'kw' ? range(inp) : inp.value;
        var n = cards.filter(function (c) { return matches(c, f, name) && optMatch(name, c, val); }).length;
        var inData = cards.some(function (c) { return optMatch(name, c, val); });
        out.textContent = n ? '(' + n + ')' : '';
        opt.classList.toggle('is-hidden', !inData && !inp.checked);      // значений нет в данных: не показываем
        opt.classList.toggle('is-disabled', n === 0 && !inp.checked);
        inp.disabled = n === 0 && !inp.checked;
        if (!opt.classList.contains('is-hidden')) anyVisible = true;
      });
      grp.classList.toggle('is-hidden', !anyVisible);
    });
  }

  // «Показать ещё N» для длинных списков
  function limitGroups() {
    [].slice.call(form.querySelectorAll('.filter-group[data-limit]')).forEach(function (grp) {
      var limit = parseInt(grp.dataset.limit, 10), btn = grp.querySelector('.filter-more');
      var opts = [].slice.call(grp.querySelectorAll('.filter-opt:not(.is-hidden)'));
      var expanded = grp.dataset.expanded === '1';
      var hiddenCount = 0;
      opts.forEach(function (o, i) {
        var hide = !expanded && i >= limit && !o.querySelector('input').checked;
        o.style.display = hide ? 'none' : '';
        if (hide) hiddenCount++;
      });
      if (btn) { btn.hidden = !(hiddenCount || expanded); btn.textContent = expanded ? 'Свернуть' : 'Показать ещё ' + hiddenCount; }
    });
  }

  function sortCards(list) {
    var mode = sortSel.value, dir = dirBtn.dataset.dir === 'desc' ? -1 : 1;
    function val(c) { return mode === 'price' ? num(c.dataset.priceMin) : num(c.dataset.kwMin); }
    return list.slice().sort(function (a, b) {
      if (mode === 'name') return dir * a.dataset.title.localeCompare(b.dataset.title, 'ru');
      if (mode === 'price' || mode === 'kw') {
        var va = val(a), vb = val(b);
        if (va === null) return 1; if (vb === null) return -1;
        return dir * (va - vb);
      }
      return dir * (num(a.dataset.order) - num(b.dataset.order));
    });
  }

  function plural(n) { var m = n % 10, h = n % 100; if (m === 1 && h !== 11) return 'серия'; if (m >= 2 && m <= 4 && !(h >= 12 && h <= 14)) return 'серии'; return 'серий'; }

  function activeCount(f) {
    return f.brand.length + f.series.length + f.inverter.length + f.hp.length + f.eff.length + f.kw.length + (f.pmin !== null || f.pmax !== null ? 1 : 0) + (f.noise !== null ? 1 : 0);
  }

  function writeUrl(f) {
    var p = new URLSearchParams();
    if (state.type) p.set('type', state.type);
    if (f.brand.length) p.set('brand', f.brand.join(','));
    if (f.series.length) p.set('series', f.series.join(','));
    if (f.inverter.length) p.set('inverter', f.inverter.join(','));
    if (f.hp.length) p.set('hp', f.hp.join(','));
    if (f.eff.length) p.set('eff', f.eff.join(','));
    if (f.kw.length) p.set('kw', checked('kw').join(','));
    if (f.pmin !== null) p.set('pmin', f.pmin);
    if (f.pmax !== null) p.set('pmax', f.pmax);
    if (f.noise !== null) p.set('noise', f.noise);
    if (sortSel.value !== 'default') p.set('sort', sortSel.value);
    if (dirBtn.dataset.dir === 'desc') p.set('dir', 'desc');
    if (state.view === 'list') p.set('view', 'list');
    var q = p.toString();
    try { history.replaceState(null, '', location.pathname + (q ? '?' + q : '') + location.hash); } catch (e) { /* адрес не меняем, если нельзя */ }
  }

  function readUrl() {
    var p = new URLSearchParams(location.search);
    function setList(name, key) { var v = (p.get(key || name) || '').split(',').filter(Boolean); inputs(name).forEach(function (i) { i.checked = v.indexOf(i.value) >= 0; }); }
    ['brand', 'series', 'inverter', 'hp', 'eff', 'kw'].forEach(function (n) { setList(n); });
    form.elements.pmin.value = p.get('pmin') || ''; form.elements.pmax.value = p.get('pmax') || '';
    var nz = p.get('noise'); inputs('noise').forEach(function (i) { i.checked = i.value === (nz || ''); });
    state.type = ['wall', 'multi', 'semi', 'mobile'].indexOf(p.get('type')) >= 0 ? p.get('type') : '';
    if (['name', 'price', 'kw'].indexOf(p.get('sort')) >= 0) sortSel.value = p.get('sort');
    if (p.get('dir') === 'desc') setDir('desc');
    setView(p.get('view') === 'list' ? 'list' : 'tiles');
    syncChips();
  }

  function syncChips() { chips.forEach(function (c) { var on = c.dataset.type === state.type; c.classList.toggle('is-active', on); c.setAttribute('aria-pressed', on ? 'true' : 'false'); }); }
  function setDir(d) { dirBtn.dataset.dir = d; dirBtn.setAttribute('aria-label', 'Направление сортировки: ' + (d === 'desc' ? 'по убыванию' : 'по возрастанию')); }
  function setView(v) { state.view = v; grid.classList.toggle('is-list', v === 'list'); viewBtns.forEach(function (b) { var on = b.dataset.view === v; b.classList.toggle('is-active', on); b.setAttribute('aria-pressed', on ? 'true' : 'false'); }); }

  function apply() {
    var f = collect();
    var shown = 0;
    cards.forEach(function (c) { var ok = matches(c, f, null); c.hidden = !ok; if (ok) shown++; });
    sortCards(cards).forEach(function (c) { grid.appendChild(c); });
    countEl.textContent = 'Найдено: ' + shown + ' ' + plural(shown);
    emptyEl.hidden = shown !== 0;
    if (applyCount) applyCount.textContent = shown + ' ' + plural(shown);
    var n = activeCount(f);
    if (badge) { badge.hidden = n === 0; badge.textContent = n; }
    updateCounts(f);
    limitGroups();
    writeUrl(f);
  }

  // панель фильтров на телефоне
  function openPanel(open) {
    if (!panel) return;
    panel.classList.toggle('is-open', open);
    overlay.hidden = !open;
    document.body.style.overflow = open && mobile.matches ? 'hidden' : '';
    if (open && closeBtn) closeBtn.focus(); else if (!open && openBtn && mobile.matches) openBtn.focus();
  }
  if (openBtn) openBtn.addEventListener('click', function () { openPanel(true); });
  if (closeBtn) closeBtn.addEventListener('click', function () { openPanel(false); });
  if (applyBtn) applyBtn.addEventListener('click', function () { openPanel(false); });
  if (overlay) overlay.addEventListener('click', function () { openPanel(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && panel && panel.classList.contains('is-open')) openPanel(false); });

  chips.forEach(function (c) { c.addEventListener('click', function () { state.type = c.dataset.type; syncChips(); apply(); }); });
  form.addEventListener('change', apply);
  form.addEventListener('input', function (e) { if (e.target.type === 'number') apply(); });
  form.addEventListener('reset', function () { setTimeout(function () { form.elements.pmin.value = ''; form.elements.pmax.value = ''; [].slice.call(form.querySelectorAll('.filter-group')).forEach(function (g) { g.dataset.expanded = ''; }); apply(); }, 0); });
  form.addEventListener('click', function (e) {
    var more = e.target.closest('.filter-more'); if (!more) return;
    var grp = more.closest('.filter-group'); grp.dataset.expanded = grp.dataset.expanded === '1' ? '' : '1'; limitGroups();
  });
  sortSel.addEventListener('change', apply);
  dirBtn.addEventListener('click', function () { setDir(dirBtn.dataset.dir === 'desc' ? 'asc' : 'desc'); apply(); });
  viewBtns.forEach(function (b) { b.addEventListener('click', function () { setView(b.dataset.view); apply(); }); });

  readUrl();
  apply();
})();
