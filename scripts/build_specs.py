"""Раскатка характеристик и документации: для каждой страницы сайта собирает data/specs/<имя>.yaml и static/docs/<бренд>/<серия>/.

  python scripts/build_specs.py [ключ_страницы ...]     (без аргументов: все страницы)

Сопоставление «страница сайта -> серии Бриза» лежит в SPECS ниже. Берутся только наши модели (артикулы с нашего сайта, их написание не меняется),
только цифры характеристик и PDF; описания с Бриза не копируются. Если на странице несколько таблиц (серий), у каждой свой подзаголовок.
Файл данных называется <страница>-<slug> (для моделей каталога это имя подхватывается автоматически), у Roland имя указано в front matter (specs:).
"""
import hashlib
import json
import os
import re
import sys
import tomllib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_breez as fb  # noqa: E402
from gallery_sources import SOURCES  # noqa: E402

ROOT = fb.ROOT
B = 'https://breez.ru/products/'


def S(*slugs):
    return [B + s + '/' for s in slugs]


# ключ страницы -> список таблиц (заголовок или None, [серии Бриза]); несколько серий в одной таблице = цвета/исполнения одной линейки
SPECS = {
    'hisense-nastennye/sensation-slider-pro': [(None, S('sensation-slider-pro-superior-dc-inverter', 'sensation-slider-pro-carbon-superior-dc-inverter'))],
    'hisense-nastennye/vision-pro-2-0': [(None, S('vision-pro-2-0-superior-dc-inverter', 'vision-pro-2-0-carbon-superior-dc-inverter'))],
    'hisense-nastennye/vibe-pro-eu': [(None, S('vibe-pro-silver-eu-dc-inverter', 'vibe-pro-carbon-eu-dc-inverter', 'vibe-pro-champagne-eu-dc-inverter'))],
    'hisense-nastennye/expert-pro-2-0-eu': [(None, S('expert-pro-2-0-eu-dc-inverter'))],
    'hisense-nastennye/goal-2-0': [('Инверторные', S('split-system-goal-2-0-dc-inverter-wi-fi')), ('Классические (on/off)', S('split-system-goal-2-0-classic-a-wi-fi'))],
    'promyshlennye/kassetnye': [
        ('Классические HEAVY 2.0 (on/off)', S('heavy-2-0-classic-casset')),
        ('Инверторные HEAVY EU DC Inverter A++', S('split-sistem-kasset-heavy-eu-dc-inverter-wi-fi', 'split-sistem-kasset-heavy-eu-dc-inverter'))],
    'promyshlennye/kanalnye': [
        ('Классические HEAVY 2.0 (on/off)', S('heavy-2-0-classic-canal')),
        ('Инверторные HEAVY EU DC Inverter A++', S('split-sistem-kanal-heavy-eu-dc-inverter-r32-wi-fi', 'split-sistem-kanal-heavy-eu-dc-inverter-r32'))],
    'promyshlennye/napolno-potolochnye': [
        ('Классические HEAVY 2.0 (on/off)', S('heavy-2-0-classic-pol-potolok')),
        ('Инверторные HEAVY EU DC Inverter A++', S('split-sistem-pol-potolok-heavy-eu-dc-inverter-r32-wi-fi', 'split-sistem-pol-potolok-heavy-eu-dc-inverter-r32',
                                                  'split-sistem-konsol-eu-dc-inverter-r32-wi-fi', 'split-sistem-konsol-eu-dc-inverter-r32'))],
    'promyshlennye/kolonnye': [(None, S('heavy-2-0-classic-kolon'))],
    'hisense-multi-split/naruzhnye-bloki': [
        ('Наружные блоки Multi EU DC Inverter (R32)', S('multi-eu-dc-inverter')),
        ('Наружные блоки Multi EU DC Inverter LP (R32)', S('multi-eu-dc-inverter-lp')),
        ('Наружные блоки Ultra Multi DC Inverter (R410A)', S('ultra-multi-dc-inverter'))],
    'hisense-multi-split/vnutrennie-bloki': [
        ('Настенные: Sensation Slider Pro Multi Superior DC Inverter', S('sensation-pro-multi-superior-dc-inverter', 'sensation-pro-carbon-multi-superior-dc-inverter')),
        ('Настенные: Vision Pro 2.0 Multi Superior DC Inverter', S('vision-pro-2-0-multi-superior-dc-inverter', 'vision-pro-2-0-carbon-multi-superior-dc-inverter')),
        ('Настенные: Vibe Pro Multi EU DC Inverter', S('vibe-pro-multi-eu-dc-inverter', 'vibe-pro-silver-multi-eu-dc-inverter', 'vibe-pro-champagne-multi-eu-dc-inverter', 'vibe-pro-carbon-multi-eu-dc-inverter')),
        ('Настенные: Zoom Multi EU DC Inverter', S('zoom-multi-eu-dc-inverter')),
        ('Консольные: Multi EU DC Inverter', S('multi-eu-dc-inverter-console')),
        ('Канальные: Multi EU DC Inverter', S('multi-eu-dc-inverter-canal')),
        ('Кассетные: Multi EU DC Inverter', S('multi-eu-dc-inverter-casset')),
        ('Напольно-потолочные: Multi EU DC Inverter', S('multi-eu-dc-inverter-pol-potolok'))],
    'hisense-mobilnye/seriya-v': [(None, S('mob-cond-v'))],
    'hisense-mobilnye/seriya-w': [(None, S('mob-cond-w'))],
    'hisense-mobilnye/seriya-c': [(None, S('mob-cond-c'))],
    'lg/deluxe-pro': [(None, S('invert-split-system-deluxe-pro-dual-inverter'))],
    'lg/artcool-mirror': [(None, S('invert-spit-system-artcool-mirror'))],
    'lg/procool': [(None, S('procool'))],
    'lg/promulti-2-0': [
        ('Наружные блоки', S('lg-promult-2025')),
        ('Внутренние блоки — настенные, серия Standard', S('lg-mult-standart')),
        ('Внутренние блоки — канальные', S('lg-mult-canal')),
        ('Внутренние блоки — настенные, серия Deluxe Pro', S('vnutr-block-mult-nasten-deluxe-pro')),
        ('Внутренние блоки — настенные, серия ARTCOOL Mirror', S('vnutr-block-mult-split-nasten-artcool-mirror')),
        ('Внутренние блоки — настенные, серия ARTCOOL Gallery', S('artcool-gallery')),
        ('Внутренние блоки — кассетные однопоточные', S('vnutr-block-mult-split-odnopotochn-casset'))],
    'royal-clima/royal-supremo': [(None, S('royal-supremo-blanco-inv', 'royal-supremo-nero-inv'))],
    'royal-clima/royal-fresh': [('Royal Fresh', S('royal-fresh-full-dc-inverter')), ('Royal Fresh Standard', S('royal-fresh-standard-full-dc-inverter'))],
    'royal-clima/felicita-heat-pump': [(None, S('felicita-heat-pump-full-dc-eu-inverter'))],
    'royal-clima/felicita-inverter': [(None, S('felicita-inverter'))],
    'royal-clima/felicita': [(None, S('felicita'))],
    'ventilyaciya/brizery/brezza-rcb-150-lux': [(None, S('brezza'))],
    'ventilyaciya/brizery/brezza-xs-rcb-75': [(None, S('brezza-xs'))],
    'ventilyaciya/brizery/brezza-luna-rcb-80-lux': [(None, S('brezza-luna'))],
    'ventilyaciya/pritochnye/vento-rcv': [(None, S('kpy-vento'))],
    'ventilyaciya/rekuperatory/fiato-rcf-70': [(None, S('energoeffektivniy-rekuperator-fiato'))],
    'ventilyaciya/rekuperatory/soffio-uno': [(None, S('soffio-uno'))],
    'ventilyaciya/rekuperatory/soffio-uno-4-0': [(None, S('soffio-uno-4-0'))],
    'ventilyaciya/rekuperatory/soffio-primo-3-0': [(None, S('soffio-primo-3-0'))],
    'ventilyaciya/rekuperatory/soffio-primo-4-0': [(None, S('soffio-primo-4-0'))],
    'osushiteli/bytovye/carisma-studio': [(None, S('carisma-studio-rd-cr'))],
    'osushiteli/bytovye/carisma-loft': [(None, S('carisma-loft-rd-cr'))],
    'osushiteli/bytovye/carisma-villa': [(None, S('carisma-villa-rd-cr'))],
    'osushiteli/bytovye/pacific-studio': [(None, S('osushit-pacific-studio'))],
    'osushiteli/bytovye/pacific-loft': [(None, S('osushit-pacific-loft'))],
    'osushiteli/bytovye/pacific-villa': [(None, S('pacific-villa'))],
    'osushiteli/bytovye/pacific-palazzo': [(None, S('pacific-palazzo'))],
    'osushiteli/bytovye/hisense-air-go-pro': [(None, S('osushit-vozd-air-go-pro'))],
    'osushiteli/dlya-basseynov/riviera': [(None, S('riviera'))],
    'favorite-ii': [(None, S('classic-favorite-2-2024'))],
    'favorite-ii-inverter': [(None, S('invert-favorite-2-2024'))],
    'maestro': [('Классические (on/off)', S('classic-split-system-maestro')), ('Инверторные', S('invert-split-system-maestro'))],
}

# Имя модели у нас -> под каким именем искать на Бризе (наше название на сайте не меняется)
ALIASES = {'RD-PC-40-E': 'RD-PC40-E'}
# Страницы Roland: имя файла данных и префикс PDF (остальные: <страница>-<slug>)
FILENAMES = {'favorite-ii': 'roland-favorite-ii', 'favorite-ii-inverter': 'roland-favorite-ii-inverter', 'maestro': 'roland-maestro'}
DOCNAMES = {'favorite-ii': 'roland-favorite-ii-2024', 'favorite-ii-inverter': 'roland-favorite-ii-inverter-2024'}


def our_models():
    cat = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
    clim = json.load(open(os.path.join(ROOT, 'data', 'climate.json'), encoding='utf-8'))
    models = tomllib.load(open(os.path.join(ROOT, 'data', 'models.toml'), 'rb'))
    pages = dict(cat['pages'])
    pages.update(clim['pages'])
    out = {}
    for page, d in models.items():
        for sid, m in d.items():
            sec = next((s for s in pages.get(page, []) if s['id'] == sid), None)
            rows = []
            for t in (sec or {}).get('tables', []):
                for r in t['rows']:
                    name = r.get('model') or r.get('name')
                    if name and name not in rows:
                        rows.append(name)
            out[f"{page}/{m['slug']}"] = rows
    for slug in ('favorite-ii', 'favorite-ii-inverter', 'maestro'):
        txt = open(os.path.join(ROOT, 'content', 'projects', slug, 'index.md'), encoding='utf-8').read()
        rows = []
        for line in txt.splitlines():
            mm = re.match(r'\|\s*([A-Z]{2,4}-[^|\s]+)\s*\|', line)
            if mm and mm.group(1) not in rows:
                rows.append(mm.group(1))
        out[slug] = rows
    return out


def build(key, ours):
    brand = SOURCES[key][0]
    folder = key.split('/')[-1]
    fname = FILENAMES.get(key) or key.replace('/', '-')
    wanted = ours[key]
    tables, docs_seen, docs, big, report = [], {}, [], [], []
    for title, urls in SPECS[key]:
        parts = []
        used = []
        for url in urls:
            ms, groups, _ = fb.fetch_series(url, wanted, ALIASES)
            if ms:
                parts.append((ms, groups))
                used.append(url)
        if not parts:
            report.append(f'  таблица «{title or "-"}»: совпадений нет')
            continue
        models, groups = fb.merge_tables(parts, wanted) if len(parts) > 1 else parts[0]
        tables.append({'title': title or '', 'source': used[0], 'models': models, 'groups': groups})
        for url in used:
            slug = url.rstrip('/').split('/')[-1]
            found = fb.find_docs(url, os.path.join(fb.CACHE, slug + '.html'))
            prefix = DOCNAMES.get(key) or f'{brand}-{slug}'
            got, bg = fb.download_docs(found, brand, folder, lambda u, p=prefix: p)
            for g in got:
                h = hashlib.md5(open(os.path.join(ROOT, 'static', g['file'].lstrip('/')), 'rb').read()).hexdigest()
                if h in docs_seen:      # тот же файл под другой серией (цвет): храним один раз
                    if docs_seen[h] != g['file']:
                        os.remove(os.path.join(ROOT, 'static', g['file'].lstrip('/')))
                    continue
                docs_seen[h] = g['file']
                docs.append(g)
            big += bg
    matched = {m for t in tables for m in t['models']}
    missing = [w for w in wanted if w not in matched and ALIASES.get(w) not in matched]
    if not tables:
        return None, report, missing, big
    d = {'brand': brand, 'tables': tables, 'docs': docs}
    dst = os.path.join(ROOT, 'data', 'specs', fname + '.yaml')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w', encoding='utf-8', newline='\n').write(fb.dump_yaml(d))
    stat = f'{fname}: наших {len(wanted)}, с характеристиками {len(matched)}, таблиц {len(tables)}, PDF {len(docs)}'
    return stat, report, missing, big


def main():
    ours = our_models()
    keys = sys.argv[1:] or list(SPECS)
    total_pdf = 0
    all_big, all_missing = [], {}
    for key in keys:
        try:
            stat, report, missing, big = build(key, ours)
        except RuntimeError as e:
            print(f'{key}: ОШИБКА {e}')
            continue
        print(stat or f'{key}: данных нет')
        for r in report:
            print(r)
        if missing:
            all_missing[key] = missing
        all_big += big
    for k, v in all_missing.items():
        print('нет на Бризе', k, v)
    for u, s in all_big:
        print(f'PDF больше 15 МБ не сохранён: {u} ({s / 1048576:.1f} МБ)')
    sz = 0
    n = 0
    for dp, _, fs in os.walk(os.path.join(ROOT, 'static', 'docs')):
        for f in fs:
            n += 1
            sz += os.path.getsize(os.path.join(dp, f))
    print(f'PDF в static/docs: {n}, всего {sz / 1048576:.0f} МБ')


if __name__ == '__main__':
    main()
