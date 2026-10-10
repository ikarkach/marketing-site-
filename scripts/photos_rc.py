"""Фото вентиляции и осушителей: публичные страницы каталога поставщика (breez.ru) -> WebP до 1000 px в content/projects/<подраздел>/.

Вызывается из build_royalclima.py --photos. Скачивает через curl (Python и Node здесь нестабильно ходят в сеть), кэш: RC_IMG_CACHE
(по умолчанию %TEMP%/rc_img). Какое фото к какой серии — задано вручную в PHOTOS (ракурсы выбраны по контактным листам).
Нужен Pillow. Обработка (прозрачный фон, обрезка полей, сжатие) — photos._prepare.
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photos  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://images.breez.ru/catalog/'
CACHE = os.environ.get('RC_IMG_CACHE') or os.path.join(tempfile.gettempdir(), 'rc_img')

# (страница-подраздел, id серии) -> [(путь на images.breez.ru/catalog/, подпись alt)]
PHOTOS = {
    ('ventilyaciya/brizery', 'rcb-150-lux'): [
        ('royal-clima/brezza/brezza-02.png', 'Бризер Royal Clima BREZZA RCB 150 LUX — общий вид'),
        ('royal-clima/brezza/brezza-03.png', 'Бризер Royal Clima BREZZA RCB 150 LUX с пультом и приложением для смартфона')],
    ('ventilyaciya/brizery', 'rcb-75'): [
        ('royal-clima/brezza-xs/brezza-xs-01.png', 'Бризер Royal Clima BREZZA XS RCB 75 — вид спереди')],
    ('ventilyaciya/brizery', 'rcb-80-lux'): [
        ('royal-clima/brezza-luna/brezza-luna-01.png', 'Бризер Royal Clima BREZZA LUNA RCB 80 LUX — общий вид'),
        ('royal-clima/brezza-luna/brezza-luna-03.png', 'Бризер Royal Clima BREZZA LUNA RCB 80 LUX — вид сбоку')],
    ('ventilyaciya/pritochnye', 'vento'): [
        ('royal-clima/kpy-vento/kpy-vento-01.png', 'Приточная установка Royal Clima VENTO RCV — общий вид'),
        ('royal-clima/kpy-vento/kpy-vento-02.png', 'Сенсорный пульт управления приточной установки Royal Clima VENTO')],
    ('ventilyaciya/rekuperatory', 'rcf-70'): [
        ('royal-clima/energoeffektivniy-rekuperator-fiato/energoeffektivniy-rekuperator-fiato-01.png', 'Приточно-вытяжная установка Royal Clima FIATO RCF 70 — вид спереди'),
        ('royal-clima/energoeffektivniy-rekuperator-fiato/energoeffektivniy-rekuperator-fiato-02.png', 'Приточно-вытяжная установка Royal Clima FIATO RCF 70 — вид под углом')],
    ('ventilyaciya/rekuperatory', 'soffio-uno'): [
        ('royal-clima/soffio-uno/soffio-uno-01.png', 'Приточно-вытяжная установка Royal Clima SOFFIO UNO'),
        ('royal-clima/soffio-uno/soffio-uno-02.png', 'Приточно-вытяжная установка Royal Clima SOFFIO UNO — вид под углом')],
    ('ventilyaciya/rekuperatory', 'soffio-uno-4-0'): [
        ('royal-clima/soffio-uno-4-0/soffio-uno-4-0-01.png', 'Приточно-вытяжная установка Royal Clima SOFFIO UNO 4.0'),
        ('royal-clima/soffio-uno-4-0/soffio-uno-4-0-02.png', 'Приточно-вытяжная установка Royal Clima SOFFIO UNO 4.0 — вид под углом')],
    ('ventilyaciya/rekuperatory', 'soffio-primo-3-0'): [
        ('royal-clima/soffio-primo-3-0/soffio-primo-3-0-01.png', 'Приточно-вытяжная установка Royal Clima SOFFIO PRIMO 3.0'),
        ('royal-clima/soffio-primo-3-0/soffio-primo-3-0-02.png', 'Приточно-вытяжная установка Royal Clima SOFFIO PRIMO 3.0 — вид под углом')],
    ('ventilyaciya/rekuperatory', 'soffio-primo-4-0'): [
        ('royal-clima/soffio-primo-4-0/soffio-primo-4-0-01.png', 'Приточно-вытяжная установка Royal Clima SOFFIO PRIMO 4.0'),
        ('royal-clima/soffio-primo-4-0/soffio-primo-4-0-02.png', 'Приточно-вытяжная установка Royal Clima SOFFIO PRIMO 4.0 — вид под углом')],
    ('osushiteli/bytovye', 'carisma-studio'): [
        ('royal-clima/carisma-studio-rd-cr/carisma-studio-rd-cr-01.png', 'Осушитель воздуха Royal Clima CARISMA Studio — общий вид'),
        ('royal-clima/carisma-studio-rd-cr/carisma-studio-rd-cr-04.png', 'Осушитель воздуха Royal Clima CARISMA Studio — вид сбоку')],
    ('osushiteli/bytovye', 'carisma-loft'): [
        ('royal-clima/carisma-loft-rd-cr/carisma-loft-rd-cr-01.png', 'Осушитель воздуха Royal Clima CARISMA Loft — общий вид'),
        ('royal-clima/carisma-loft-rd-cr/carisma-loft-rd-cr-03.png', 'Осушитель воздуха Royal Clima CARISMA Loft — вид сбоку')],
    ('osushiteli/bytovye', 'carisma-villa'): [
        ('royal-clima/carisma-villa-rd-cr/carisma-villa-rd-cr-01.png', 'Осушитель воздуха Royal Clima CARISMA Villa — общий вид'),
        ('royal-clima/carisma-villa-rd-cr/carisma-villa-rd-cr-03.png', 'Осушитель воздуха Royal Clima CARISMA Villa — вид под углом')],
    ('osushiteli/bytovye', 'pacific-studio'): [
        ('royal-clima/osushit-pacific-studio/osushit-pacific-studio-01.png', 'Осушитель воздуха Royal Clima PACIFIC Studio — вид спереди'),
        ('royal-clima/osushit-pacific-studio/osushit-pacific-studio-04.png', 'Осушитель воздуха Royal Clima PACIFIC Studio — вид под углом')],
    ('osushiteli/bytovye', 'pacific-loft'): [
        ('royal-clima/osushit-pacific-lof/osushit-pacific-loft-01.png', 'Осушитель воздуха Royal Clima PACIFIC Loft — вид спереди'),
        ('royal-clima/osushit-pacific-lof/osushit-pacific-loft-02.png', 'Осушитель воздуха Royal Clima PACIFIC Loft — вид под углом')],
    ('osushiteli/bytovye', 'pacific-villa'): [
        ('royal-clima/pacific-villa/pacific-villa-01.png', 'Осушитель воздуха Royal Clima PACIFIC Villa — вид спереди'),
        ('royal-clima/pacific-villa/pacific-villa-02.png', 'Осушитель воздуха Royal Clima PACIFIC Villa — вид под углом')],
    ('osushiteli/bytovye', 'pacific-palazzo'): [
        ('royal-clima/pacific-palazzo/pacific-palazzo-04.png', 'Осушитель воздуха Royal Clima PACIFIC Palazzo — вид под углом'),
        ('royal-clima/pacific-palazzo/pacific-palazzo-01.png', 'Осушитель воздуха Royal Clima PACIFIC Palazzo — вид спереди')],
    ('osushiteli/bytovye', 'hisense-air-go-pro'): [
        ('hisense/osushit-vozd-air-go-pro/osushit-vozd-air-go-pro-02.png', 'Осушитель воздуха Hisense Air Go Pro — общий вид'),
        ('hisense/osushit-vozd-air-go-pro/osushit-vozd-air-go-pro-03.png', 'Осушитель воздуха Hisense Air Go Pro — вид под углом')],
    ('osushiteli/dlya-basseynov', 'riviera'): [
        ('royal-clima/riviera/riviera-01.png', 'Осушитель воздуха Royal Clima RIVIERA для бассейнов')],
}


def _get(path):
    dst = os.path.join(CACHE, path.replace('/', os.sep))
    if not (os.path.exists(dst) and os.path.getsize(dst) > 1000):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        for _ in range(5):
            r = subprocess.run(['curl', '-s', '-f', '--max-time', '40', '-o', dst, BASE + path])
            if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 1000:
                break
        else:
            raise RuntimeError(f'не удалось скачать {BASE + path}')
    with open(dst, 'rb') as f:
        return f.read()


def export(pages, series):
    """Сохраняет WebP рядом с подразделом и дописывает images в секции и image в серии."""
    total = 0
    by_id = {s['id']: s for s in series}
    for (page, sid), imgs in PHOTOS.items():
        sec = next((s for s in pages.get(page, []) if s['id'] == sid), None)
        if not sec:
            print(f'  фото пропущено: нет серии {page}/{sid}')
            continue
        outdir = os.path.join(ROOT, 'content', 'projects', *page.split('/'))
        os.makedirs(outdir, exist_ok=True)
        sec['images'] = []
        for n, (path, alt) in enumerate(imgs, 1):
            im = photos._prepare(_get(path))
            name = f'{sid}-{n}.webp'
            full = os.path.join(outdir, name)
            im.save(full, 'WEBP', quality=84, method=6)
            sec['images'].append(dict(file=name, alt=alt, w=im.width, h=im.height))
            total += os.path.getsize(full)
        ser = by_id.get(f"{page.replace('/', '-')}-{sid}")
        if ser and sec['images']:
            ser['image'] = dict(page=page, file=sec['images'][0]['file'])
    print(f'Фото: {sum(len(s["images"]) for v in pages.values() for s in v)} шт., {total // 1024} КБ')
