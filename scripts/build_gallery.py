"""Собирает галереи моделей: оригиналы из source-images/ -> WebP в static/images/models/ + data/gallery.json.

  python scripts/build_gallery.py

Вход:  scripts/gallery_manifest.json — для каждой модели список выбранных фото в нужном порядке
       (вид спереди -> под углом -> наружный блок -> пульт -> прочее), не больше 12 штук.
Выход: static/images/models/<бренд>/<модель>/NN.webp   (основное фото, холст 1200x900, белый фон)
                                              NN-t.webp (миниатюра 200x150)
       data/gallery.json  (адреса и подписи alt; читает layouts/partials/gallery.html)
Оригиналы (source-images/) в репозиторий не попадают. Нужен Pillow.
"""
import json
import os
import sys

from PIL import Image, ImageChops

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gallery_sources import SOURCES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source-images')
OUT = os.path.join(ROOT, 'static', 'images', 'models')
MAIN = (1200, 900)
THUMB = (200, 150)
QUALITY = 80


def flatten(path):
    im = Image.open(path)
    im = im.convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert('RGB')


def trim(im, margin=0.05):
    """Обрезает пустые белые поля и оставляет ровный отступ, чтобы предметы на разных фото выглядели соразмерно."""
    diff = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).convert('L').point(lambda v: 255 if v > 12 else 0)
    box = diff.getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    m = int(max(x1 - x0, y1 - y0) * margin)
    return im.crop((max(0, x0 - m), max(0, y0 - m), min(im.width, x1 + m), min(im.height, y1 + m)))


def canvas(im, size, max_up=1.3):
    w, h = size
    k = min(w / im.width, h / im.height)
    k = min(k, max_up)
    nw, nh = max(1, round(im.width * k)), max(1, round(im.height * k))
    im = im.resize((nw, nh), Image.LANCZOS)
    c = Image.new('RGB', size, (255, 255, 255))
    c.paste(im, ((w - nw) // 2, (h - nh) // 2))
    return c


def main():
    manifest = json.load(open(os.path.join(ROOT, 'scripts', 'gallery_manifest.json'), encoding='utf-8'))
    result = {}
    stats = []
    for key, m in manifest.items():
        brand = SOURCES[key][0]
        slug = key.split('/')[-1]
        src_dir = os.path.join(SRC, brand, slug)
        out_dir = os.path.join(OUT, brand, slug)
        os.makedirs(out_dir, exist_ok=True)
        for f in os.listdir(out_dir):
            os.remove(os.path.join(out_dir, f))
        items = []
        for i, p in enumerate(m['photos'][:12], 1):
            n = f'{i:02d}'
            im = canvas(trim(flatten(os.path.join(src_dir, p['file']))), MAIN)
            im.save(os.path.join(out_dir, n + '.webp'), 'WEBP', quality=QUALITY, method=6)
            im.resize(THUMB, Image.LANCZOS).save(os.path.join(out_dir, n + '-t.webp'), 'WEBP', quality=QUALITY, method=6)
            alt = m['name'] + ' — ' + p['kind'] + (', ' + p['variant'] if p.get('variant') else '')
            items.append({'n': n, 'alt': alt})
        result[key] = {'dir': f'/images/models/{brand}/{slug}', 'items': items}
        stats.append((key, len(items)))
    with open(os.path.join(ROOT, 'data', 'gallery.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    for key, n in stats:
        print(f'{key}: {n}')
    print('моделей:', len(stats), 'фото:', sum(n for _, n in stats))


if __name__ == '__main__':
    main()
