"""Royal Clima (вентиляция и осушители) из прайс-листа -> data/climate.json.

  python scripts/build_royalclima.py --xlsx <ROYAL CLIMA.xlsx> [--photos]

Публикуются только розничные цены: колонка «РИЦ». Колонки «Дилерская цена», «Ваша Спец цена» и «Розница» не читаются вообще.
У бытовых осушителей CARISMA и PACIFIC в прайсе формулы с ошибками (#REF!): характеристик и цен нет, на сайте — «Цена по запросу».
Привязка блоков прайса к сериям задана вручную (номера строк ниже): структура листа нерегулярная.
Тексты страниц (описания, заголовки) — в data/models.toml. Hisense Air Go Pro берётся из data/catalog.json (блок osushiteli).
"""
import argparse
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

    return pages, series


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', required=True)
    ap.add_argument('--photos', action='store_true', help='скачать фото с breez.ru и сжать (нужен Pillow, scripts/photos_rc.py)')
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
    out = OrderedDict(priceDate='08.06.2026', source='Royal Clima, прайс-лист с 08.06.2026 (РИЦ)', pages=pages, series=series)
    with open(os.path.join(ROOT, 'data', 'climate.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    n = sum(len(v) for v in pages.values())
    print(f'серий: {n}; позиций: {sum(len(t["rows"]) for v in pages.values() for s in v for t in s["tables"])}')


if __name__ == '__main__':
    main()
