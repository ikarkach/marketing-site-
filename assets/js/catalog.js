/* Каталог: фильтры, вкладки типов и сортировка карточек серий. Без библиотек. Все карточки есть в HTML, поэтому ссылки видны поисковикам. */
(function () {
  var grid = document.getElementById('catalog-grid');
  var form = document.getElementById('catalog-filters');
  if (!grid || !form) return;
  var cards = [].slice.call(grid.children);
  var tabs = [].slice.call(document.querySelectorAll('.catalog-tab[data-type]'));
  var count = document.getElementById('catalog-count');
  var empty = document.getElementById('catalog-empty');
  var sortSel = document.getElementById('catalog-sort');
  var box = document.getElementById('catalog-filters-box');
  var type = '';

  // на телефоне фильтры свёрнуты
  if (box && window.matchMedia('(max-width: 768px)').matches) box.open = false;

  function num(v) { var n = parseFloat(v); return isNaN(n) ? null : n; }
  function checked(name) { return [].slice.call(form.querySelectorAll('input[name="' + name + '"]:checked')); }
  function values(name) { return checked(name).map(function (i) { return i.value; }); }
  function ranges(name) { return checked(name).map(function (i) { return [num(i.dataset.min), num(i.dataset.max)]; }); }
  function overlaps(lo, hi, r) { return lo !== null && hi !== null && hi >= r[0] && lo <= r[1]; }

  function visible(c, f) {
    var d = c.dataset;
    if (type && d.type !== type) return false;
    if (f.brands.length && f.brands.indexOf(d.brand) < 0) return false;
    if (f.techs.length && !f.techs.some(function (t) { return d.tech === t || d.tech === 'both'; })) return false;
    if (f.effs.length) {
      var e = (d.eff || '').split(' ');
      if (!f.effs.some(function (x) { return e.indexOf(x) >= 0; })) return false;
    }
    if (f.kw.length && !f.kw.some(function (r) { return overlaps(num(d.kwMin), num(d.kwMax), r); })) return false;
    if (f.price.length && !f.price.some(function (r) { return overlaps(num(d.priceMin), num(d.priceMax), r); })) return false;
    if (f.noise !== null) { var n = num(d.noise); if (n === null || n > f.noise) return false; }
    return true;
  }

  function plural(n) {
    var m = n % 10, h = n % 100;
    if (m === 1 && h !== 11) return 'серия';
    if (m >= 2 && m <= 4 && !(h >= 12 && h <= 14)) return 'серии';
    return 'серий';
  }

  function apply() {
    var noiseEl = form.querySelector('input[name="noise"]:checked');
    var f = {
      brands: values('brand'), techs: values('tech'), effs: values('eff'),
      kw: ranges('kw'), price: ranges('price'),
      noise: noiseEl && noiseEl.value ? num(noiseEl.value) : null
    };
    var shown = 0;
    cards.forEach(function (c) { var ok = visible(c, f); c.hidden = !ok; if (ok) shown++; });
    count.textContent = 'Найдено: ' + shown + ' ' + plural(shown);
    empty.hidden = shown !== 0;
    sortCards();
  }

  function sortCards() {
    var mode = sortSel.value;
    var list = cards.slice();
    function price(c) { var p = num(c.dataset.priceMin); return p === null ? Infinity : p; }
    list.sort(function (a, b) {
      if (mode === 'title') return a.dataset.title.localeCompare(b.dataset.title, 'ru');
      if (mode === 'price-asc') return price(a) - price(b);
      if (mode === 'price-desc') { var pa = price(a), pb = price(b); if (pa === Infinity) return 1; if (pb === Infinity) return -1; return pb - pa; }
      return num(a.dataset.order) - num(b.dataset.order);
    });
    list.forEach(function (c) { grid.appendChild(c); });
  }

  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      type = t.dataset.type;
      tabs.forEach(function (x) { var on = x === t; x.classList.toggle('is-active', on); x.setAttribute('aria-pressed', on ? 'true' : 'false'); });
      apply();
    });
  });
  form.addEventListener('change', apply);
  sortSel.addEventListener('change', apply);
  form.addEventListener('reset', function () { setTimeout(apply, 0); });

  apply();
})();
