/* Галерея фото модели (разметка: layouts/partials/gallery.html).
   Большое фото + полоса миниатюр, стрелки, клавиши ←/→, свайп на телефоне, увеличение по клику (окно <dialog>, Esc закрывает).
   Без библиотек. Остальные фото подгружаются только при переключении (кроме миниатюр). */
(function () {
  var roots = [].slice.call(document.querySelectorAll('[data-gallery]'));
  if (!roots.length) return;
  var box = null;

  function Gallery(root) {
    var self = this;
    this.root = root;
    this.img = root.querySelector('.gallery__img');
    this.thumbs = [].slice.call(root.querySelectorAll('.gallery__thumb'));
    this.cur = 0;
    this.items = this.thumbs.map(function (t) { return { src: t.getAttribute('data-full'), alt: t.getAttribute('data-alt') }; });
    this.count = root.querySelector('[data-gallery-cur]');
    if (!this.items.length) this.items = [{ src: this.img.getAttribute('src'), alt: this.img.getAttribute('alt') }];

    root.querySelector('.gallery__zoom').addEventListener('click', function () { openBox(self); });
    this.thumbs.forEach(function (t, i) { t.addEventListener('click', function () { self.go(i); }); });
    var p = root.querySelector('.gallery__nav--prev'), n = root.querySelector('.gallery__nav--next');
    if (p) p.addEventListener('click', function () { self.go(self.cur - 1); });
    if (n) n.addEventListener('click', function () { self.go(self.cur + 1); });
    root.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { self.go(self.cur - 1); e.preventDefault(); }
      else if (e.key === 'ArrowRight') { self.go(self.cur + 1); e.preventDefault(); }
    });
    swipe(root.querySelector('.gallery__stage'), function (d) { self.go(self.cur + d); });
  }

  Gallery.prototype.go = function (i, quiet) {
    var len = this.items.length;
    if (len < 2) return;
    this.cur = (i + len) % len;
    var it = this.items[this.cur];
    this.img.src = it.src;
    this.img.alt = it.alt;
    this.img.removeAttribute('fetchpriority');
    if (this.count) this.count.textContent = this.cur + 1;
    var cur = this.cur;
    this.thumbs.forEach(function (t, k) {
      t.classList.toggle('is-active', k === cur);
      if (k === cur) t.setAttribute('aria-current', 'true'); else t.removeAttribute('aria-current');
    });
    var t = this.thumbs[cur], list = t.parentNode.parentNode;
    list.scrollTo({ left: t.parentNode.offsetLeft - (list.clientWidth - t.parentNode.offsetWidth) / 2, behavior: quiet ? 'auto' : 'smooth' });
    // заранее грузим соседнее фото, чтобы переключение было мгновенным
    var nx = this.items[(cur + 1) % len];
    if (nx) (new Image()).src = nx.src;
  };

  /* свайп влево/вправо: порог 40 px, вертикальная прокрутка страницы не мешает */
  function swipe(el, cb) {
    var x0 = null, y0 = 0;
    el.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
    el.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      x0 = null;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.5) { cb(dx < 0 ? 1 : -1); suppressClick(el); }
    }, { passive: true });
  }
  function suppressClick(el) {
    var h = function (e) { e.stopImmediatePropagation(); e.preventDefault(); };
    el.addEventListener('click', h, true);
    setTimeout(function () { el.removeEventListener('click', h, true); }, 350);
  }

  /* увеличенное фото */
  function openBox(g) {
    if (!box) {
      var d = document.createElement('dialog');
      d.className = 'gallery-box';
      d.setAttribute('aria-label', 'Фото на весь экран');
      d.innerHTML = '<button type="button" class="gallery-box__close" aria-label="Закрыть">×</button>' +
        '<button type="button" class="gallery-box__nav gallery-box__nav--prev" aria-label="Предыдущее фото">‹</button>' +
        '<img class="gallery-box__img" alt="">' +
        '<button type="button" class="gallery-box__nav gallery-box__nav--next" aria-label="Следующее фото">›</button>' +
        '<p class="gallery-box__cap"></p>';
      document.body.appendChild(d);
      box = { el: d, img: d.querySelector('.gallery-box__img'), cap: d.querySelector('.gallery-box__cap'), g: null };
      d.querySelector('.gallery-box__close').addEventListener('click', function () { d.close(); });
      d.querySelector('.gallery-box__nav--prev').addEventListener('click', function () { step(-1); });
      d.querySelector('.gallery-box__nav--next').addEventListener('click', function () { step(1); });
      d.addEventListener('click', function (e) { if (e.target === d) d.close(); });
      d.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') { step(-1); e.preventDefault(); }
        else if (e.key === 'ArrowRight') { step(1); e.preventDefault(); }
      });
      swipe(d, function (dir) { step(dir); });
      d.addEventListener('close', function () { document.documentElement.classList.remove('gallery-lock'); });
    }
    box.g = g;
    show();
    if (g.items.length < 2) box.el.classList.add('is-single'); else box.el.classList.remove('is-single');
    if (typeof box.el.showModal === 'function') box.el.showModal(); else box.el.setAttribute('open', '');
    document.documentElement.classList.add('gallery-lock');
  }
  function show() {
    var it = box.g.items[box.g.cur];
    box.img.src = it.src;
    box.img.alt = it.alt;
    box.cap.textContent = it.alt + (box.g.items.length > 1 ? ' (' + (box.g.cur + 1) + ' из ' + box.g.items.length + ')' : '');
  }
  function step(d) {
    box.g.go(box.g.cur + d, true);
    show();
  }

  roots.forEach(function (r) { new Gallery(r); });
})();
