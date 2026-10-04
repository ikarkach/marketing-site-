"""Фото серий из прайс-листов: вынимает изображения из xlsx, сжимает до веба (WebP, до 800 px) и кладёт рядом со страницей.

Какое фото к какой серии относится, определено по положению картинок в листах прайсов (см. PHOTOS ниже).
Нужен Pillow:  pip install pillow
"""
import io
import os
import zipfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_SIDE = 800

# страница -> секция -> [(файл прайса, имя картинки в xl/media, подпись)]
PHOTOS = {
    'hisense-nastennye': {
        'sensation': [('H', 'image56.png', 'Hisense Sensation Slider Pro — внутренний блок')],
        'vibe': [('H', 'image48.png', 'Hisense Vibe Pro — серебристый'), ('H', 'image49.png', 'Hisense Vibe Pro — чёрный'),
                 ('H', 'image50.png', 'Hisense Vibe Pro — шампань')],
        'expert': [('H', 'image47.png', 'Hisense Expert Pro — внутренний блок')],
        'goal': [('H', 'image16.png', 'Hisense Goal 2.0 — внутренний блок')],
        'city': [('H', 'image40.png', 'Hisense City 2.0 — внутренний блок')],
        'strong': [('H', 'image61.png', 'Hisense Strong Vibe Classic A — внутренний блок')],
    },
    'promyshlennye': {
        'kass': [('H', 'image97.png', 'Hisense кассетный кондиционер')],
        'duct': [('H', 'image98.png', 'Hisense канальный кондиционер')],
        'floor': [('H', 'image100.png', 'Hisense напольно-потолочный кондиционер')],
    },
    'hisense-mobilnye': {
        'mobile-v': [('H', 'image162.png', 'Hisense мобильный кондиционер')],
    },
    'lg': {
        'deluxepro': [('L', 'image8.png', 'LG Deluxe Pro — внутренний блок')],
        'artcoolmirror': [('L', 'image4.png', 'LG ARTCOOL Mirror — внутренний блок')],
        'procool': [('L', 'image5.png', 'LG ProCool — внутренний блок')],
        'promulti': [('L', 'image6.png', 'LG ProMulti 2.0 — схема мульти-сплит системы')],
    },
}


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
            for n, (src, media, alt) in enumerate(imgs, 1):
                im = Image.open(io.BytesIO(zips[src].read('xl/media/' + media)))
                im = im.convert('RGBA')
                bbox = im.getchannel('A').getbbox()  # обрезаем прозрачные поля
                if bbox:
                    im = im.crop(bbox)
                im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
                name = f'{sid}-{n}.webp'
                im.save(os.path.join(outdir, name), 'WEBP', quality=82, method=6)
                sec['images'].append(dict(file=name, alt=alt, w=im.width, h=im.height))
                total += os.path.getsize(os.path.join(outdir, name))
    print(f'Фото: {sum(len(s["images"]) for secs in finalized.values() for s in secs)} шт., {total // 1024} КБ')
