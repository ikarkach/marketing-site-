"""Скачивает оригиналы фото из публичных галерей серий breez.ru в source-images/ (папка не коммитится: .gitignore).

  python scripts/fetch_breez_gallery.py [ключ_страницы ...]

Страницы серий: https://breez.ru/products/<серия>/ (открытые, вход не нужен; личный кабинет не используется).
Раскладка: source-images/<бренд сайта>/<последняя часть адреса модели>/<серия breez>__<имя файла>.png
Сеть: через curl (Python и Node здесь нестабильно ходят в интернет); повторы при сбоях.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gallery_sources import SOURCES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source-images')
CACHE = os.environ.get('BREEZ_HTML_CACHE') or os.path.join(os.environ.get('TEMP', '.'), 'breez_html')
UA = 'Mozilla/5.0 (compatible; Usplit catalog build)'


def curl(url, dst, minsize=1000):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for _ in range(5):
        r = subprocess.run(['curl', '-s', '-f', '--max-time', '60', '-A', UA, '-o', dst, url])
        if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > minsize:
            return True
    return False


def gallery_urls(slug):
    """Полноразмерные адреса фото из галереи серии (ссылки data-fancybox на странице серии)."""
    name = slug.strip('/').split('/')[-1]
    dst = os.path.join(CACHE, f'prod_{name}.html')
    if not (os.path.exists(dst) and os.path.getsize(dst) > 5000):
        if not curl('https://breez.ru' + slug, dst, 5000):
            raise RuntimeError(f'не открылась страница серии {slug}')
    t = open(dst, encoding='utf-8').read()
    hrefs = re.findall(r'href="(https://images\.breez\.ru/catalog/[^"]+)" data-fancybox="gallery"', t)
    return list(dict.fromkeys(hrefs))


def main():
    keys = sys.argv[1:] or list(SOURCES)
    total = fail = 0
    for key in keys:
        brand, slugs = SOURCES[key]
        folder = os.path.join(SRC, brand, key.split('/')[-1])
        for slug in slugs:
            sname = slug.strip('/').split('/')[-1]
            try:
                urls = gallery_urls(slug)
            except RuntimeError as e:
                print('ОШИБКА', e); fail += 1; continue
            for u in urls:
                fname = f"{sname}__{u.rsplit('/', 1)[-1]}"
                dst = os.path.join(folder, fname)
                if os.path.exists(dst) and os.path.getsize(dst) > 1000:
                    total += 1; continue
                if curl(u, dst):
                    total += 1
                else:
                    fail += 1; print('НЕ СКАЧАНО', u)
        print(f'{key}: готово')
    print(f'фото: {total}, ошибок: {fail}')


if __name__ == '__main__':
    main()
