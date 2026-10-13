"""Royal Clima (вентиляция, осушители, настенные сплит-системы) из прайс-листа -> data/climate.json.

  python scripts/build_royalclima.py --xlsx <ROYAL CLIMA.xlsx> [--photos] [--split-photos]
  (нужен полный прайс со всеми листами: «ВЕНТИЛЯЦИОННОЕ ОБОРУДОВАНИЕ», «ОСУШИТЕЛИ», листы сплит-систем)

Публикуются только розничные цены: колонка «РИЦ». Колонки «Дилерская цена», «Ваша Спец цена» и «Розница» не читаются вообще.
У бытовых осушителей CARISMA и PACIFIC в прайсе формулы с ошибками (#REF!): характеристик и цен нет, на сайте — «Цена по запросу».
Привязка блоков прайса к сериям задана вручную (номера строк ниже): структура листа нерегулярная.
Тексты страниц (описания, заголовки) — в data/models.toml. Hisense Air Go Pro берётся из data/catalog.json (блок osushiteli).
"""
import argparse
import io
import json
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsx_reader as xr  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S_DEHUM, S_VENT = 'ОСУШИТЕЛИ', 'ВЕНТИЛЯЦИОННОЕ ОБОРУДОВАНИЕ'

# --- подразделы и серии: (страница-подраздел, id серии, название, строки описания, строки моделей, колонки описания)
VENT = [
    ('ventilyaciya/brizery', 'rcb-150-lux', 'Royal Clima BREZZA RCB 150 LUX', range(5, 13), [13, 14], [9]),
    ('ventilyaciya/brizery', 'rcb-75', 'Royal Clima BREZZA XS RCB 75', range(17, 24), [24], [9]),
    ('ventilyaciya/brizery', 'rcb-80-lux', 'Royal Clima BREZZA LUNA RCB 80 LUX', range(25, 32), [32], [9]),
    ('ventilyaciya/pritochnye', 'vento', 'Royal Clima VENTO RCV', range(42, 50), [50, 51, 52, 53, 54, 55], [9]),
    ('ventilyaciya/rekuperatory', 'rcf-70', 'Royal Clima FIATO RCF 70', range(34, 40), [40, 41], [9]),
    ('ventilyaciya/rekuperatory', 'soffio-uno', 'Royal Clima SOFFIO UNO', range(57, 65), [65, 66], [9]),
    ('ventilyaciya/rekuperatory', 'soffio-uno-4-0', 'Royal Clima SOFFIO UNO 4.0', range(69, 76), [77, 78, 79, 80], [9]),
    ('ventilyaciya/rekuperatory', 'soffio-primo-3-0', 'Royal Clima SOFFIO PRIMO 3.0', range(88, 95), [96, 97, 98, 99, 100, 101, 102], [9]),
    ('ventilyaciya/rekuperatory', 'soffio-primo-4-0', 'Royal Clima SOFFIO PRIMO 4.0', range(105, 112), [112, 113, 114], [9]),
]
# комплектующие, относящиеся к серии (строки листа): фильтры, нагреватели, датчики, Wi-Fi модули, пульты
VENT_ACC = {
    'rcb-150-lux': [15, 122, 123],
    'rcb-75': [130],
    'rcb-80-lux': [137],
    'vento': [150, 151, 152, 153],
    'rcf-70': [144, 145],
    'soffio-uno': [157, 162, 163, 170, 180, 181],
    'soffio-uno-4-0': [176, 177, 178, 179],
    'soffio-primo-3-0': [164, 165, 171],
    'soffio-primo-4-0': [186, 187, 188, 192, 193, 194],
}
# осушители: бытовые (без характеристик и цен: в прайсе #REF!) и RIVIERA
DEHUM = [
    ('osushiteli/bytovye', 'carisma-studio', 'Royal Clima CARISMA Studio', range(6, 14), [14], [8, 10]),
    ('osushiteli/bytovye', 'carisma-loft', 'Royal Clima CARISMA Loft', range(15, 22), [22, 23], [8, 10]),
    ('osushiteli/bytovye', 'carisma-villa', 'Royal Clima CARISMA Villa', range(24, 32), [32, 33], [8, 10]),
    ('osushiteli/bytovye', 'pacific-studio', 'Royal Clima PACIFIC Studio', range(34, 42), [42, 43], [8, 10]),
    ('osushiteli/bytovye', 'pacific-loft', 'Royal Clima PACIFIC Loft', range(44, 51), [51], [8, 10]),
    ('osushiteli/bytovye', 'pacific-villa', 'Royal Clima PACIFIC Villa', range(52, 60), [60], [8, 10]),
    ('osushiteli/bytovye', 'pacific-palazzo', 'Royal Clima PACIFIC Palazzo', range(61, 68), [68], [8, 10]),
    ('osushiteli/dlya-basseynov', 'riviera', 'Royal Clima RIVIERA', range(69, 75), [75, 76, 77, 78], [8, 10]),
]
SKIP_TEXT = ('УЗНАТЬ БОЛЬШЕ', 'узнать больше')

# --- настенные сплит-системы (страница content/projects/royal-clima): листы полного прайса Royal Clima.
# Строка комплекта: 3 — артикул внутр. блока (…/IN), 4 — модель, 5/6 — охлаждение/нагрев кВт, 7 — шум, 8 — класс,
# 14 — РИЦ за комплект (внутр. + наруж. блок). Колонки 12, 13, 15, 16 (цены блоков, дилерские, спец) не читаются.
# Особенности — текст значков из шапки серии в прайсе (там он разбит по ячейкам, поэтому собран вручную).
S_SUPREMO, S_FRESH = 'СПЛИТ-СИСТЕМА ROYAL SUPREMO', 'СПЛИТ-СИСТЕМА С ПРИТОЧНОЙ ВЕНТ'
S_INV, S_CLASSIC = 'ИНВЕРТОРНЫЕ СПЛИТ-СИСТЕМЫ', 'КЛАССИЧЕСКИЕ СПЛИТ-СИСТЕМЫ'
SPLIT_PAGE = 'royal-clima'
SPLITS = [
    dict(sid='supremo', title='Royal Clima ROYAL SUPREMO', tech='yes', sheet=S_SUPREMO,
         tables=[('Royal Supremo Nero', [66, 68, 70, 72]), ('Royal Supremo Blanco', [85, 87, 89, 91])],
         images=[(53, 4), (72, 4)],
         features=['Полностью инверторная (Full DC Inverter), высокая энергоэффективность', 'Любое направление потока воздуха',
                   '7 скоростей вентилятора внутреннего блока', 'Мягкое распределение воздушного потока',
                   'Биполярный ионизатор воздуха', 'Фильтры тонкой очистки Active Carbon и Silver Ion', 'UV-обработка воздуха',
                   'Тише шелеста листьев: от 19 дБ(А)', 'Работа на охлаждение до −15 °C', 'Голосовое управление через Яндекс.Алису',
                   'Расширенная гарантия 3+2 года']),
    dict(sid='fresh', title='Royal Clima ROYAL FRESH', tech='yes', sheet=S_FRESH,
         tables=[('Royal Fresh', [66, 68]), ('Royal Fresh Standard', [102, 104])],
         acc=[109, 110],
         images=[(92, 5), (56, 4)],   # первым — фото на белом фоне
         features=['Встроенная приточная вентиляция: свежий воздух с улицы без открытого окна', 'Фильтр HEPA H11 на притоке',
                   'Полностью инверторная (Full DC Inverter), высокая энергоэффективность', 'Встроенное управление по Wi-Fi, Яндекс.Алиса',
                   '7 скоростей вентилятора внутреннего блока', 'Равномерное мягкое распределение воздушного потока',
                   'Тихая работа: от 18 дБ(А) у Royal Fresh, от 19,5 дБ(А) у Royal Fresh Standard', 'Royal Fresh: любое направление потока воздуха, UV-обработка воздуха',
                   'Royal Fresh Standard: функция 3D Auto Air', 'Расширенная гарантия 3+2 года']),
    dict(sid='felicita-heat-pump', title='Royal Clima FELICITA HEAT PUMP', tech='yes', sheet=S_INV,
         tables=[(None, [15, 17, 19, 21])],
         images=[(6, 5)],
         features=['Работа на охлаждение и обогрев до −30 °C', 'Полностью инверторная (Full DC Inverter), высокая энергоэффективность',
                   'Самоочистка замораживанием', 'Функция I FEEL', 'Функция 3D Auto Air', 'Управление по Wi-Fi, Яндекс.Алиса',
                   'Фильтры Active Carbon и Silver Ion', 'Низкий уровень шума: от 18,2 дБ(А)', 'Расширенная гарантия 3+2 года']),
    dict(sid='felicita-inverter', title='Royal Clima FELICITA Inverter', tech='yes', sheet=S_INV,
         tables=[(None, [91, 93, 95, 97, 99, 101, 103, 105])],
         images=[(81, 4)],
         features=['Инверторный компрессор', 'Встроенный Wi-Fi модуль, Яндекс.Алиса', 'Функция I FEEL',
                   'Функция 3D Auto Air и фильтры Silver Ion, Active Carbon (модели 22, 28, 35)',
                   '7 скоростей вентилятора внутреннего блока (модели, произведённые после 01.12.2025)',
                   'Работа на охлаждение и обогрев до −15 °C', 'Шумоизоляция компрессора',
                   'Антикоррозийное покрытие теплообменников Golden Fin']),
    dict(sid='felicita', title='Royal Clima FELICITA', tech='no', sheet=S_CLASSIC,
         tables=[(None, [105, 107, 109, 111, 113])],
         images=[(94, 4)],
         features=['Классический (on/off) компрессор', 'Встроенный Wi-Fi модуль, Яндекс.Алиса', 'Функция I FEEL', 'Функция 3D Auto Air',
                   'Фильтры Silver Ion и Active Carbon (модели 22, 28, 35)', '4 скорости вентилятора внутреннего блока',
                   'Шумоизоляция компрессора', 'Антикоррозийное покрытие теплообменников Golden Fin',
                   'Работа на охлаждение до −40 °C с зимним комплектом']),
]


def txt(v):
    return re.sub(r'\s+', ' ', str(v)).strip() if v not in (None, '') else ''


def good(v):
    t = txt(v)
    return t and not t.startswith('#') and t not in ('x', '-', '—')


def price(v):
    try:
        n = float(str(v).replace(' ', '').replace(',', '.'))
    except ValueError:
        return None
    return int(round(n)) if n > 0 else None


def num(v):
    t = txt(v)
    if not good(t):
        return None
    try:
        f = float(t.replace(',', '.'))
    except ValueError:
        return t
    return int(f) if f == int(f) else round(f, 3)


def features(rows, cells_rows, cols):
    out = []
    for rn in cells_rows:
        for c in cols:
            t = txt(rows.get(rn, {}).get(c))
            if not t or t in SKIP_TEXT or t.upper() in SKIP_TEXT or t.startswith('**'):
                continue
            t = re.sub(r'^\*([\w-]+)\s+', r'\1: ', t)  # «*RD-PC12-EW Встроенный…» -> «RD-PC12-EW: встроенный…»
            t = re.sub(r'(\d)м²', r'\1 м²', t)
            if t.count('(') > t.count(')'):  # в исходном тексте бывает потеряна закрывающая скобка
                t += ')'
            if t not in out:
                out.append(t[0].upper() + t[1:] if t[0].islower() else t)
    return out


def maxnum(s):
    ns = [float(x.replace(',', '.')) for x in re.findall(r'\d+(?:[.,]\d+)?', str(s or ''))]
    return max(ns) if ns else None


def vent_rows(rows, nums):
    out = []
    prev = {}
    for rn in nums:
        c = rows[rn]
        r = OrderedDict(model=txt(c.get(3)) or txt(c.get(2)), flow=txt(c.get(4)), noise=txt(c.get(5)), volt=txt(c.get(6)),
                        dims=txt(c.get(9)), weight=num(c.get(10)), price=price(c.get(12)))   # c.get(12) = РИЦ
        for k in ('flow', 'noise', 'volt', 'dims', 'weight'):      # одинаковый базовый блок: пустые ячейки берём из строки выше
            if r[k] in ('', None) and k in prev and rn - 1 in nums:
                r[k] = prev[k]
        prev = r
        r['model'] = r['model'].replace('  ', ' ')
        out.append(dict(r))
    return out


def acc_rows(rows, nums):
    out = []
    for rn in nums:
        c = rows[rn]
        name = txt(c.get(3)) or txt(c.get(2))
        desc = txt(c.get(4))
        if desc and desc[0].islower():
            desc = desc[0].upper() + desc[1:]
        if good(c.get(9)) and str(c.get(9)).strip().startswith('Срок службы'):
            desc = (desc + '. ' if desc else '') + txt(c.get(9)).rstrip('*')
        out.append(dict(name=name, desc=desc or None, article=txt(c.get(2)), price=price(c.get(12))))
    return out


def facts_vent(rows):
    fl = [maxnum(r['flow']) for r in rows if maxnum(r['flow'])]
    nz = [maxnum(r['noise']) for r in rows if r['noise'] and not str(r['noise']).startswith('до')]
    nmin = []
    for r in rows:
        ns = [float(x.replace(',', '.')) for x in re.findall(r'\d+(?:[.,]\d+)?', r['noise'])]
        if ns and not r['noise'].startswith('до'):
            nmin.append(min(ns))
    f = []
    if fl:
        f.append(dict(l='Расход воздуха', v=(f'до {int(max(fl))} м³/ч' if min(fl) == max(fl) else f'от {int(min(fl))} до {int(max(fl))} м³/ч')))
    if nmin:
        f.append(dict(l='Уровень звукового давления', v=f'от {int(min(nmin)) if min(nmin) == int(min(nmin)) else min(nmin)} дБ(А)'))
    return f


def kw_nominal(v):
    """'2,90 (0,80-3,50)' -> '2,9'; 2.4 -> '2,4'."""
    t = re.sub(r'\(.*?\)', '', txt(v)).strip()
    try:
        f = float(t.replace(',', '.'))
    except ValueError:
        return t or None
    return ('%.2f' % f).rstrip('0').rstrip('.').replace('.', ',')


def noise_range(v):
    ns = [float(x.replace(',', '.')) for x in re.findall(r'\d+(?:[.,]\d+)?', txt(v))]
    if not ns:
        return None
    f = lambda x: ('%g' % x).replace('.', ',')  # noqa: E731
    return f(min(ns)) if min(ns) == max(ns) else f'{f(min(ns))}–{f(max(ns))}'


def kit_rows(sheet, nums):
    out = []
    for rn in nums:
        c = sheet[rn]
        assert txt(c.get(3)).endswith('/IN'), f'строка {rn}: ожидался внутренний блок, а там {c.get(3)!r}'
        out.append(dict(model=re.sub(r'\s+NEW$', '', txt(c.get(4))), cool=kw_nominal(c.get(5)), heat=kw_nominal(c.get(6)),
                        eff=txt(c.get(8)), noise=noise_range(c.get(7)), price=price(c.get(14))))   # c.get(14) = РИЦ комплекта
    return out


def split_stats(rows, tech):
    def first(s):
        m = re.match(r'(\d+(?:,\d+)?)', s or '')
        return float(m.group(1).replace(',', '.')) if m else None
    kws = [k for k in (first(r['cool']) for r in rows) if k is not None]
    nz = [k for k in (first(r['noise']) for r in rows) if k is not None]
    effs = sorted({r['eff'].split('/')[0] for r in rows if r.get('eff')})
    st = stats(rows)
    st.update(tech=tech, hp='yes' if any(r.get('heat') for r in rows) else 'no',
              kwMin=min(kws) if kws else None, kwMax=max(kws) if kws else None, noiseMin=min(nz) if nz else None, eff=effs)
    return st


def build_splits(wb, add):
    for s in SPLITS:
        sh = wb[s['sheet']]
        tables, allrows = [], []
        for ttl, nums in s['tables']:
            rows = kit_rows(sh, nums)
            allrows += rows
            tables.append(dict(title=ttl, kind='kit', rows=rows))
        if s.get('acc'):
            acc = [dict(name=txt(sh[rn].get(3)), desc=txt(sh[rn].get(4)) or None, article=txt(sh[rn].get(2)), price=price(sh[rn].get(14)))
                   for rn in s['acc']]
            tables.append(dict(title='Комплектующие', kind='acc', rows=acc))
        images = [dict(file=f"{s['sid']}-{i + 1}.webp", alt=f"{s['title']}") for i in range(len(s['images']))]
        sec = dict(id=s['sid'], title=s['title'], images=images, features=s['features'], note=None, tables=tables)
        extra = split_stats(allrows, s['tech'])
        extra['image'] = dict(page=SPLIT_PAGE, file=images[0]['file'])
        add(SPLIT_PAGE, s['sid'], s['title'], 'wall', sec, extra)


def export_split_photos(xlsx):
    """Фото серий — картинки, вставленные в прайс рядом с заголовком серии (лист, строка, колонка привязки) -> WebP."""
    import posixpath
    import zipfile
    from PIL import Image
    z = zipfile.ZipFile(xlsx)
    rels = z.read('xl/_rels/workbook.xml.rels').decode()
    rid = {m.group(1): m.group(2) for m in re.finditer(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)}
    rid.update({m.group(2): m.group(1) for m in re.finditer(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', rels)})
    sheets = {m.group(1): 'xl/' + rid[m.group(2)].lstrip('/').replace('xl/', '')
              for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', z.read('xl/workbook.xml').decode())}

    def anchors(sheet):
        out = {}
        srel = posixpath.join(posixpath.dirname(sheet), '_rels', posixpath.basename(sheet) + '.rels')
        for d in re.findall(r'Target="([^"]*drawing[^"]*)"', z.read(srel).decode()):
            dp = posixpath.normpath(posixpath.join(posixpath.dirname(sheet), d))
            drel = posixpath.join(posixpath.dirname(dp), '_rels', posixpath.basename(dp) + '.rels')
            dmap = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', z.read(drel).decode()))
            for a in re.finditer(r'<xdr:(?:twoCellAnchor|oneCellAnchor)[^>]*>(.*?)</xdr:(?:twoCellAnchor|oneCellAnchor)>',
                                 z.read(dp).decode(), re.S):
                fr = re.search(r'<xdr:from><xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>', a.group(1), re.S)
                emb = re.search(r'r:embed="(rId\d+)"', a.group(1))
                if fr and emb:
                    out[(int(fr.group(2)) + 1, int(fr.group(1)) + 1)] = posixpath.normpath(
                        posixpath.join(posixpath.dirname(dp), dmap[emb.group(1)]))
        return out

    dst = os.path.join(ROOT, 'content', 'projects', SPLIT_PAGE)
    os.makedirs(dst, exist_ok=True)
    for s in SPLITS:
        an = anchors(sheets[s['sheet']])
        for i, pos in enumerate(s['images']):
            im = Image.open(io.BytesIO(z.read(an[pos]))).convert('RGBA')
            im.thumbnail((1000, 1000))
            im.save(os.path.join(dst, f"{s['sid']}-{i + 1}.webp"), 'WEBP', quality=85, method=6)


def keep_photos(pages, series):
    """Фото вентиляции и осушителей добавляет photos_rc.export (--photos, скачивание). Без него переносим их из прежнего файла."""
    path = os.path.join(ROOT, 'data', 'climate.json')
    if not os.path.exists(path):
        return
    old = json.load(open(path, encoding='utf-8'))
    for page, secs in pages.items():
        prev = {s['id']: s for s in old.get('pages', {}).get(page, [])}
        for s in secs:
            if not s.get('images') and prev.get(s['id'], {}).get('images'):
                s['images'] = prev[s['id']]['images']
    prev_series = {s['id']: s for s in old.get('series', [])}
    for s in series:
        if not s.get('image') and prev_series.get(s['id'], {}).get('image'):
            s['image'] = prev_series[s['id']]['image']


def stats(rows):
    p = [r['price'] for r in rows if r.get('price')]
    return dict(models=len(rows), priceMin=min(p) if p else None, priceMax=max(p) if p else None)


def build(xlsx, models):
    wb = xr.load(xlsx)
    vent, deh = wb[S_VENT], wb[S_DEHUM]
    pages = OrderedDict()
    series = []

    def add(page, sid, title, typ, sec, extra):
        pages.setdefault(page, []).append(sec)
        m = models.get(page, {}).get(sid, {})
        slug = m.get('slug', sid)
        series.append(dict(id=f"{page.replace('/', '-')}-{sid}", title=title, brand='Royal Clima', type=typ,
                           url=f'/projects/{page}/{slug}/', page=page, sid=sid, **extra))

    for page, sid, title, desc_rows, mrows, dcols in VENT:
        rows = vent_rows(vent, mrows)
        tables = [dict(title=None, kind='vent', rows=rows)]
        acc = acc_rows(vent, VENT_ACC.get(sid, []))
        if acc:
            tables.append(dict(title='Опции и комплектующие', kind='acc', rows=acc))
        sec = dict(id=sid, title=title, images=[], features=features(vent, desc_rows, dcols), facts=facts_vent(rows),
                   note=None, tables=tables)
        if sid == 'rcb-150-lux':
            sec['note'] = 'Уровень звукового давления указан в окружении на расстоянии 1,5 м.'
        add(page, sid, title, 'vent', sec, stats(rows))

    for page, sid, title, desc_rows, mrows, dcols in DEHUM:
        pool = sid == 'riviera'
        rows = []
        for rn in mrows:
            c = deh[rn]
            if pool:
                rows.append(dict(model=txt(c.get(2)), perday=num(c.get(4)), noise=txt(c.get(6)), dims=txt(c.get(7)),
                                 weight=num(c.get(8)), price=price(c.get(9))))      # c.get(9) = РИЦ; колонки 10, 11 не читаются
            else:
                rows.append(dict(model=txt(c.get(2)), price=None))                  # характеристик и цен в прайсе нет (#REF!)
        feats = features(deh, desc_rows, dcols)
        facts = []
        if pool:
            pd = [r['perday'] for r in rows if isinstance(r['perday'], (int, float))]
            facts.append(dict(l='Производительность', v=f'от {min(pd)} до {max(pd)} л/сут'))
        sec = dict(id=sid, title=title, images=[], features=feats, facts=facts, note=None,
                   tables=[dict(title=None, kind='dehum-pool' if pool else 'dehum-req', rows=rows)])
        add(page, sid, title, 'dehum', sec, stats(rows))

    build_splits(wb, add)
    return pages, series


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', required=True)
    ap.add_argument('--photos', action='store_true', help='скачать фото с breez.ru и сжать (нужен Pillow, scripts/photos_rc.py)')
    ap.add_argument('--split-photos', action='store_true', help='фото настенных сплит-систем из картинок прайса (нужен Pillow)')
    a = ap.parse_args()
    import tomllib
    with open(os.path.join(ROOT, 'data', 'models.toml'), 'rb') as f:
        models = tomllib.load(f)
    pages, series = build(a.xlsx, models)
    # Hisense Air Go Pro: единственная позиция из catalog.json (блок osushiteli), страница модели в «бытовых осушителях»
    cat = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
    row = cat['osushiteli'][0]
    sec = dict(id='hisense-air-go-pro', title='Hisense Air Go Pro', images=[], features=[],
               facts=[dict(l='Производительность', v=f"{row['perday']} л/сут"), dict(l='Объём бака', v=f"{row['tank']} л"),
                      dict(l='Уровень шума', v=f"{row['noise']} дБ(А)")],
               note=None, tables=[dict(title=None, kind='dehum', rows=[row])])
    pages['osushiteli/bytovye'].append(sec)
    m = models.get('osushiteli/bytovye', {}).get('hisense-air-go-pro', {})
    series.append(dict(id='osushiteli-bytovye-hisense-air-go-pro', title='Hisense Air Go Pro', brand='Hisense', type='dehum',
                       url=f"/projects/osushiteli/bytovye/{m.get('slug', 'hisense-air-go-pro')}/", page='osushiteli/bytovye',
                       sid='hisense-air-go-pro', **stats([row])))
    if a.photos:
        import photos_rc
        photos_rc.export(pages, series)
    else:
        keep_photos(pages, series)   # без --photos фото вентиляции и осушителей берём из текущего data/climate.json
    if a.split_photos:
        export_split_photos(a.xlsx)
    out = OrderedDict(priceDate='08.06.2026', source='Royal Clima, прайс-лист с 08.06.2026 (РИЦ)', pages=pages, series=series)
    with open(os.path.join(ROOT, 'data', 'climate.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    n = sum(len(v) for v in pages.values())
    print(f'серий: {n}; позиций: {sum(len(t["rows"]) for v in pages.values() for s in v for t in s["tables"])}')


if __name__ == '__main__':
    main()
