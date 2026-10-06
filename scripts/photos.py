"""Фото серий для каталога: скачивает изображения, сжимает до веба (WebP, до 1000 px) и кладёт рядом со страницей.

Источники:
  'B' — публичные фото каталога поставщика (breez.ru), использование согласовано с поставщиком;
  'H' / 'L' — картинки из прайс-листов Hisense / LG (запасной вариант, если у поставщика нет подходящего фото).
Какое фото к какой серии относится, определено вручную (см. PHOTOS ниже). Нужен Pillow:  pip install pillow
"""
import io
import os
import time
import urllib.request
import zipfile

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_SIDE = 1000
BREEZ = 'https://images.breez.ru/catalog/'


def b(path):
    return ('B', BREEZ + path)


# страница -> секция -> [(источник, адрес или имя картинки в xl/media, подпись)]
PHOTOS = {
    'hisense-nastennye': {
        'sensation': [(*b('hisense/sensation-slider-pro-superior-dc-inverter/sensation-slider-pro-superior-dc-inverter-03.png'), 'Hisense Sensation Slider Pro Superior — внутренний блок')],
        'vision': [(*b('hisense/vision-pro-2-0-superior-dc-inverter/vision-pro-2-0-superior-dc-inverter-03.png'), 'Hisense Vision Pro 2.0 Superior — внутренний блок'),
                   (*b('hisense/vision-pro-2-0-carbon-superior-dc-inverter/vision-pro-2-0-carbon-superior-dc-inverter-03.png'), 'Hisense Vision Pro 2.0 Carbon — внутренний блок')],
        'vibe': [(*b('hisense/vibe-pro-silver-eu-dc-inverter/vibe-pro-silver-eu-dc-inverter-02.png'), 'Hisense Vibe Pro — серебристый'),
                 (*b('hisense/vibe-pro-carbon-eu-dc-inverter/vibe-pro-carbon-eu-dc-inverter-03.png'), 'Hisense Vibe Pro — чёрный'),
                 (*b('hisense/vibe-pro-champagne-eu-dc-inverter/vibe-pro-champagne-eu-dc-inverter-02.png'), 'Hisense Vibe Pro — шампань')],
        'expert': [(*b('hisense/expert-pro-2-0-eu-dc-inverter/expert-pro-2-0-eu-dc-inverter-03.png'), 'Hisense Expert Pro 2.0 — внутренний блок')],
        'goal': [(*b('hisense/split-system-goal-2-0-dc-inverter-wi-fi/split-system-goal-2-0-dc-inverter-wi-fi-02.png'), 'Hisense Goal 2.0 инверторный — внутренний блок'),
                 (*b('hisense/split-system-goal-2-0-classic-a-wi-fi/split-system-goal-2-0-classic-a-wi-fi-02.png'), 'Hisense Goal 2.0 классический — внутренний блок')],
        'city': [(*b('hisense/invert-split-system-city-2-0-dc-inverter/invert-split-system-city-2-0-dc-inverter-03.png'), 'Hisense City 2.0 инверторный — внутренний блок'),
                 (*b('hisense/classic-split-system-city-a/classic-split-system-city-a-03.png'), 'Hisense City 2.0 классический — внутренний блок')],
        'zoom': [(*b('hisense/zoom-2-0-dc-inverter/zoom-2-0-dc-inverter-03.png'), 'Hisense Zoom 2.0 инверторный — внутренний блок'),
                 (*b('hisense/zoom-classic-a/zoom-classic-a-03.png'), 'Hisense Zoom 2.0 классический — внутренний блок')],
        'zoomw': [(*b('hisense/zoom-2-0-dc-inverter/zoom-2-0-dc-inverter-03.png'), 'Hisense Zoom 2.0 с зимним комплектом — внутренний блок')],
        'strong': [(*b('hisense/classic-strong-vibe-a/classic-strong-vibe-a-03.png'), 'Hisense Strong Vibe Classic A — внутренний блок')],
    },
    'promyshlennye': {
        'kass': [(*b('hisense/split-sistem-kasset-heavy-eu-dc-inverter-wi-fi/split-sistem-kasset-heavy-eu-dc-inverter-wi-fi-01.png'), 'Hisense кассетный кондиционер HEAVY')],
        'duct': [(*b('hisense/split-sistem-kanal-heavy-eu-dc-inverter-r32-wi-fi/split-sistem-kanal-heavy-eu-dc-inverter-r32-wi-fi-01.png'), 'Hisense канальный кондиционер HEAVY')],
        'floor': [(*b('hisense/split-sistem-pol-potolok-heavy-eu-dc-inverter-r32-wi-fi/split-sistem-pol-potolok-heavy-eu-dc-inverter-r32-wi-fi-01.png'), 'Hisense напольно-потолочный кондиционер HEAVY')],
        'column': [(*b('hisense/heavy-2-0-classic-kolon/heavy-2-0-classic-kolon-01.png'), 'Hisense колонный кондиционер HEAVY 2.0')],
    },
    'hisense-multi-split': {
        'outdoor': [(*b('hisense/multi-eu-dc-inverter/multi-eu-dc-inverter-01.png'), 'Hisense наружный блок мульти-сплит системы')],
        'indoor': [(*b('hisense/vibe-pro-multi-eu-dc-inverter/vibe-pro-multi-eu-dc-inverter-01.png'), 'Hisense внутренний блок мульти-сплит системы')],
    },
    'hisense-mobilnye': {
        'mobile-v': [(*b('hisense/mob-cond-v/mob-cond-v-01.png'), 'Hisense мобильный кондиционер серии V')],
        'mobile-w': [(*b('hisense/mob-cond-w/mob-cond-w-01.png'), 'Hisense мобильный кондиционер серии W')],
        'mobile-c': [(*b('hisense/mob-cond-c/mob-cond-c-01.png'), 'Hisense мобильный кондиционер серии C')],
    },
    'lg': {
        'deluxepro': [(*b('lg/invert-split-system-deluxe-pro-dual-inverter/invert-split-system-deluxe-pro-dual-inverter-03.png'), 'LG Deluxe Pro — внутренний блок')],
        'artcoolmirror': [(*b('lg/invert-spit-system-artcool-mirror/invert-spit-system-artcool-mirror-01.png'), 'LG ARTCOOL Mirror — внутренний блок')],
        'procool': [(*b('lg/procool/procool-02.png'), 'LG ProCool — внутренний блок')],
        'promulti': [(*b('lg/lg-promult-2025/lg-promult-2025-01.png'), 'LG ProMulti 2.0 — мульти-сплит система')],
    },
}


def _fetch(url):
    last = None
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Usplit catalog build)'})
            return urllib.request.urlopen(req, timeout=40).read()
        except Exception as e:  # сеть нестабильна: повторяем
            last = e
            time.sleep(1.5)
    raise RuntimeError(f'не удалось скачать {url}: {last}')


def _prepare(raw):
    im = Image.open(io.BytesIO(raw)).convert('RGBA')
    if im.getchannel('A').getextrema()[0] == 255:  # нет прозрачности: белый фон, связанный с краями, делаем прозрачным
        rgb = im.convert('RGB')
        marker = (255, 0, 255)
        for xy in ((0, 0), (rgb.width - 1, 0), (0, rgb.height - 1), (rgb.width - 1, rgb.height - 1)):
            if sum(rgb.getpixel(xy)) >= 3 * 245:
                ImageDraw.floodfill(rgb, xy, marker, thresh=14)
        px = rgb.load(); al = im.load()
        for y in range(rgb.height):
            for x in range(rgb.width):
                if px[x, y] == marker:
                    al[x, y] = (255, 255, 255, 0)
    bbox = im.getchannel('A').getbbox()  # обрезаем прозрачные поля
    if bbox:
        im = im.crop(bbox)
    im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    return im

def export(hisense, lg, finalized):
    zips = {'H': zipfile.ZipFile(hisense), 'L': zipfile.ZipFile(lg)}
    total = 0
    for page, secs in PHOTOS.items():
        outdir = os.path.join(ROOT, 'content', 'projects', page)
        os.makedirs(outdir, exist_ok=True)
        by_id = {s['id']: s for s in finalized.get(page, [])}
        for sid, imgs in secs.items():
            sec = by_id.get(sid)
            if not sec:
                print(f'  фото пропущено: нет секции {page}/{sid}')
                continue
            for n, (src, ref, alt) in enumerate(imgs, 1):
                raw = _fetch(ref) if src == 'B' else zips[src].read('xl/media/' + ref)
                im = _prepare(raw)
                name = f'{sid}-{n}.webp'
                path = os.path.join(outdir, name)
                im.save(path, 'WEBP', quality=84, method=6)
                sec['images'].append(dict(file=name, alt=alt, w=im.width, h=im.height))
                total += os.path.getsize(path)
    print(f'Фото: {sum(len(s["images"]) for secs in finalized.values() for s in secs)} шт., {total // 1024} КБ')
