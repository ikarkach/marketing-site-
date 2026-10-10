#!/usr/bin/env python3
"""Собирает data/catalog.json из прайс-листов поставщиков (xlsx).

В файл попадают ТОЛЬКО рекомендованные розничные цены (РРЦ/РИЦ). Дилерские и «спец.» цены,
внутренние коды поставщика и скрытые листы не читаются и на сайт не попадают.

  python scripts/build_catalog.py --hisense <HISENSE.xlsx> --lg <LG.xlsx> [--photos] [--include-clearance]

  --photos             вынуть фото серий из прайсов, сжать до веба (нужен Pillow) и положить в content/projects/<страница>/
  --include-clearance  не исключать позиции с пометками «Распродажа остатков» / «Ликвидация остатков»
Исходные xlsx лежат вне репозитория и не изменяются.
"""
import argparse
import io
import json
import os
import re
import sys
import zipfile
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsx_reader as xr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_RE = re.compile(r'^(НС|BR)-\d+')
PRICE_DATE = '15.09.2026'
report = {'excluded_clearance': [], 'excluded_noprice': [], 'notes': []}


# ---------- форматирование значений ----------
def txt(v):
    return re.sub(r'\s+', ' ', str(v)).strip() if v is not None else None


def num(v):
    try:
        return float(str(v).replace(' ', '').replace(',', '.'))
    except (TypeError, ValueError):
        return None


def price(v):
    p = num(v)
    return int(p + 0.5) if p and p > 0 else None  # до рубля, .5 округляется вверх


def kcap(s):
    return s.replace('к', 'K').replace('k', 'K') if s else s


def fmt_num(f):
    s = ('%.2f' % round(f, 2)).rstrip('0').rstrip('.')
    return s.replace('.', ',')


def nominal(v):
    """'2,95 (1,00-4,00)' -> '2,95'; '8,12 + 2,5' остаётся как есть."""
    if v is None:
        return None
    s = txt(re.sub(r'\(.*?\)', '', str(v)))
    if not s or s in ('-', '–'):
        return None
    if re.fullmatch(r'[\d.,]+', s):
        f = num(s)
        return fmt_num(f) if f is not None else s
    return s.replace('.', ',')


def noise(v):
    if v is None:
        return None
    vals = [num(x) for x in str(v).split('/') if num(x) is not None]
    if not vals:
        return txt(v)
    lo, hi = min(vals), max(vals)
    return fmt_num(lo) if lo == hi else f'{fmt_num(lo)}–{fmt_num(hi)}'


def eff(v):
    if v is None:
        return None
    s = txt(v)
    for a, b in (('А', 'A'), ('В', 'B'), ('С', 'C')):
        s = s.replace(a, b)
    return re.sub(r'\s*/\s*', '/', s)


def title_case(s):
    s = s.title()
    for a, b in ((' Dc ', ' DC '), (' Eu ', ' EU '), (' Fm ', ' FM '), (' Lp', ' LP'), ('Wi-Fi', 'Wi-Fi'), (' Pro', ' Pro')):
        s = s.replace(a, b)
    return s


def clean_head(s):
    s = txt(s)
    s = re.sub(r'\bWI-FI\b|\bWi-Fi\b', '', s, flags=re.I)
    s = re.sub(r'\bNEW\b|\b2026\b', '', s)
    return re.sub(r'\s+', ' ', s).strip()


# ---------- структура ----------
class Pages(OrderedDict):
    def section(self, page, sid, title, **kw):
        p = self.setdefault(page, OrderedDict())
        if sid not in p:
            p[sid] = dict(id=sid, title=title, images=[], features=[], note=kw.get('note'), tables=OrderedDict())
        return p[sid]

    @staticmethod
    def table(section, key, title, kind):
        t = section['tables']
        if key not in t:
            t[key] = dict(title=title, kind=kind, rows=[])
        return t[key]


def clearance(flag):
    return bool(flag) and ('РАСПРОДАЖА' in flag.upper() or 'ЛИКВИДАЦИЯ' in flag.upper())


# ---------- HISENSE ----------
WALL = [  # (регулярка заголовка, секция, заголовок таблицы)
    (r'SENSATION SLIDER PRO SUPERIOR', 'sensation', 'Superior'),
    (r'SENSATION SLIDER PRO CARBON', 'sensation', 'Carbon Superior'),
    (r'VISION PRO 2\.0 SUPERIOR', 'vision', 'Superior'),
    (r'VISION PRO 2\.0 CARBON', 'vision', 'Carbon Superior'),
    (r'VIBE PRO EU', 'vibe', None),
    (r'EXPERT PRO', 'expert', None),
    (r'GOAL 2\.0 DC', 'goal', 'Инверторные'),
    (r'GOAL 2\.0 CLASSIC', 'goal', 'Классические (on/off)'),
    (r'CITY 2\.0 DC', 'city', 'Инверторные'),
    (r'CITY 2\.0 CLASSIC', 'city', 'Классические (on/off)'),
    (r'ZOOM 2\.0 DC.*ЗИМНИМ', 'zoomw', 'Инверторные'),
    (r'ZOOM 2\.0 CLASSIC.*ЗИМНИМ', 'zoomw', 'Классические (on/off)'),
    (r'ZOOM 2\.0 DC', 'zoom', 'Инверторные'),
    (r'ZOOM 2\.0 CLASSIC', 'zoom', 'Классические (on/off)'),
    (r'STRONG VIBE', 'strong', None),
]
# Серии, снятые с сайта по решению владельца (2026-10-10): строки распознаём, но в каталог не берём
EXCLUDED_WALL = {'city', 'zoom', 'zoomw', 'strong'}
WALL_TITLES = OrderedDict([
    ('sensation', 'Hisense Sensation Slider Pro'),
    ('vision', 'Hisense Vision Pro 2.0'),
    ('vibe', 'Hisense Vibe Pro EU'),
    ('expert', 'Hisense Expert Pro 2.0 EU'),
    ('goal', 'Hisense Goal 2.0'),
])
SEMI_TYPES = [('КАССЕТНОГО', 'kass', 'Кассетные'), ('НАПОЛЬНО-ПОТОЛОЧНОГО', 'floor', 'Напольно-потолочные и консольные'),
              ('КОНСОЛЬНОГО', 'floor', 'Напольно-потолочные и консольные'), ('КАНАЛЬНОГО', 'duct', 'Канальные'),
              ('КОЛОННОГО', 'column', 'Колонные')]
SEMI_ORDER = ['kass', 'duct', 'floor', 'column']
IND_TYPES = [('НАСТЕННЫЕ', 'Настенные'), ('КОНСОЛЬНЫЕ', 'Консольные'), ('КАНАЛЬНЫЕ', 'Канальные'),
             ('КАССЕТНЫЕ', 'Кассетные'), ('НАПОЛЬНО-ПОТОЛОЧНЫЕ', 'Напольно-потолочные')]


def kit_row(c, ric_col=10, flag_col=13):
    return dict(model=re.sub(r'WI-FI', 'Wi-Fi', txt(c.get(2))), cool=nominal(c.get(3)), heat=nominal(c.get(4)), eff=eff(c.get(5)),
                noise=noise(c.get(6)), price=price(c.get(ric_col)), _flag=txt(c.get(flag_col)), _d=price(c.get(11)))


def build_hisense(path, pages, accessories, include_clearance):
    rows = xr.load(path)['КРАТКИЙ ПРАЙС СПЛИТЫ']
    mode = None
    cur = {}
    acc_cat = None
    for rn in sorted(rows):
        if rn < 5:
            continue
        c = rows[rn]
        code = txt(c.get(1))
        head = txt(c.get(2)) if not (code and CODE_RE.match(code)) else None
        # ---- заголовки ----
        if not (code and CODE_RE.match(code)):
            if code in ('Код', 'Артикул') or (head and head.rstrip() in ('Модель', 'Артикул')):
                continue
            if not head:
                continue
            u = head.upper()
            if u.startswith('АКСЕССУАРЫ ДЛЯ МОБИЛЬНЫХ'):
                mode, acc_cat = 'acc', 'Аксессуары для мобильных кондиционеров'; continue
            if 11 in c and 'УЗНАТЬ' in str(c[11]):  # заголовок серии
                if mode in ('wall_inv', 'wall_cls'):
                    for rx, sid, ttl in WALL:
                        if re.search(rx, u):
                            cur = dict(sid=sid, ttl=ttl)
                            break
                    else:
                        report['notes'].append(f'не опознана серия: {head}')
                        cur = {}
                elif mode == 'mobile':
                    cur = dict(sid='mobile', ttl=title_case(re.sub('МОБИЛЬНЫЕ КОНДИЦИОНЕРЫ СЕРИИ ', '', u)).replace('С', 'C'))
                elif mode == 'acc':
                    acc_cat = head
                continue
            if u.startswith('СПЕЦИАЛЬНАЯ СЕРИЯ') or u.startswith('СПЛИТ-СИСТЕМЫ ИНВЕРТОРНОГО ТИПА'):
                mode = 'wall_inv'; continue
            if u.startswith('СПЛИТ-СИСТЕМЫ КЛАССИЧЕСКОГО ТИПА'):
                mode = 'wall_cls'; continue
            if u.startswith('ПОЛУПРОМЫШЛЕННЫЕ'):
                if 'ИНВЕРТОРНОГО' in u:
                    mode, cur = 'semi', dict(var='Инверторные HEAVY EU DC Inverter A++', old=False)
                elif 'HEAVY 2.0' in u:
                    mode, cur = 'semi', dict(var='Классические HEAVY 2.0 (on/off)', old=False)
                else:
                    mode, cur = 'semi', dict(var='Классические HEAVY (on/off)', old=True)
                continue
            if mode == 'semi' and u.startswith('СПЛИТ-СИСТЕМЫ'):
                for key, sid, ttl in SEMI_TYPES:
                    if key in u:
                        cur = dict(cur, sid=sid, ttl=ttl, sub=ttl if key in ('КОНСОЛЬНОГО',) else None)
                        break
                continue
            if u.startswith('МУЛЬТИ СПЛИТ-СИСТЕМЫ'):
                mode = 'multi_out'; cur = dict(refr='R410A' if 'R410A' in u else 'R32'); continue
            if u.startswith('НАРУЖНЫЕ БЛОКИ'):
                mode = 'multi_out'
                rest = clean_head(head)[len('НАРУЖНЫЕ БЛОКИ '):]
                cur = dict(cur, ttl=f"Наружные блоки {title_case(rest)} ({cur.get('refr', 'R32')})")
                continue
            if u.startswith('УНИВЕРСАЛЬНЫЕ ВНУТРЕННИЕ'):
                mode = 'multi_in'; continue
            if mode == 'multi_in' and u.startswith('ВНУТРЕННИЕ'):
                kind_t = next((n for k, n in IND_TYPES if k in u), 'Внутренние')
                rest = clean_head(re.sub(r'^ВНУТРЕННИЕ \S+ БЛОКИ\s*', '', head, flags=re.I))
                cur = dict(ttl=f'{kind_t}: ' + title_case(rest) if rest else kind_t, type=kind_t)
                continue
            if u == 'МОБИЛЬНЫЕ КОНДИЦИОНЕРЫ':
                mode = 'mobile'; continue
            if u.startswith('БЫТОВЫЕ ОСУШИТЕЛИ'):
                mode = 'dehum'; continue
            if u.startswith('АКСЕССУАРЫ ДЛЯ МОБИЛЬНЫХ'):
                mode, acc_cat = 'acc', 'Аксессуары для мобильных кондиционеров'; continue
            if u.startswith('АКСЕССУАРЫ RAC'):
                mode = 'acc'; continue
            if mode == 'acc' or mode == 'dehum':
                if 12 in c and 'скидка' in str(c.get(11, '')).lower():
                    letters = [ch for ch in head if ch.isalpha()]
                    mostly_upper = letters and sum(ch.isupper() for ch in letters) / len(letters) > 0.6
                    mode, acc_cat = 'acc', (head.strip().capitalize() if mostly_upper else head.strip())
                continue
            if mode == 'dehum' and u == 'AIR GO PRO':
                cur = dict(ttl='Air Go Pro'); continue
            if u == 'AIR GO PRO':
                cur = dict(ttl='Air Go Pro'); continue
            continue
        # ---- строки с товаром ----
        flag = txt(c.get(13))
        if mode in ('wall_inv', 'wall_cls'):
            if not cur:
                continue
            if cur['sid'] in EXCLUDED_WALL:
                continue
            r = kit_row(c)
            sec = pages.section('hisense-nastennye', cur['sid'], WALL_TITLES[cur['sid']])
            key = cur['ttl'] or 'main'
            t = pages.table(sec, key, cur['ttl'], 'kit')
        elif mode == 'semi':
            r = kit_row(c)
            r['model'] = txt(c.get(2)).replace(' | ', ' + ')
            if r['_flag'] and clearance(r['_flag']) and not include_clearance:
                report['excluded_clearance'].append(f"{r['model']} ({r['price']} ₽)"); continue
            sec = pages.section('promyshlennye', cur['sid'], cur['ttl'])
            t = pages.table(sec, cur['var'], cur['var'], 'kit')
        elif mode == 'multi_out':
            r = dict(model=txt(c.get(2)), cool=nominal(c.get(3)), heat=nominal(c.get(4)), eff=eff(c.get(5)),
                     noise=noise(c.get(6)), pipe=nominal(c.get(7)), price=price(c.get(10)), _flag=flag, _d=price(c.get(11)))
            if not c.get(6) and not c.get(7):  # строка без шума и трассы (F15(Е)) — не наружный блок мульти-системы
                report['notes'].append(f"пропущена строка без параметров наружного блока: {r['model']} ({r['price']} ₽)")
                continue
            sec = pages.section('hisense-multi-split', 'outdoor', 'Наружные блоки мульти-сплит систем')
            t = pages.table(sec, cur.get('ttl') or 'out', cur.get('ttl'), 'outdoor')
        elif mode == 'multi_in':
            r = kit_row(c)
            if r['_flag'] and clearance(r['_flag']) and not include_clearance:
                report['excluded_clearance'].append(f"{r['model']} ({r['price']} ₽)"); continue
            sec = pages.section('hisense-multi-split', 'indoor', 'Внутренние блоки')
            t = pages.table(sec, cur['ttl'], cur['ttl'], 'indoor')
        elif mode == 'mobile':
            r = kit_row(c)
            r['heat'] = None
            sec = pages.section('hisense-mobilnye', 'mobile-' + re.sub(r'\W+', '', cur['ttl']).lower(), 'Мобильные кондиционеры серии ' + cur['ttl'])
            t = pages.table(sec, 'main', None, 'kit')
        elif mode == 'dehum':
            r = dict(model=txt(c.get(2)), perday=nominal(c.get(3)), tank=nominal(c.get(4)), air=nominal(c.get(5)),
                     noise=nominal(c.get(6)), dims=txt(c.get(7)), price=price(c.get(10)), _flag=flag, _d=price(c.get(11)))
            pages.setdefault('_osushiteli', []).append(r)
            continue
        elif mode == 'acc':
            name = re.sub(r'\s*ЛИКВИДАЦИЯ ОСТАТКОВ', '', txt(c.get(2)) or '')
            sub = txt(c.get(3))
            if sub and ('#N/A' in sub or sub.lower() == name.lower()):
                sub = None
            extra = txt(c.get(4))
            if extra and ('#N/A' in extra or extra.lower() == name.lower()):
                extra = None
            if acc_cat and acc_cat.lower().startswith('дренажные') and sub and extra:
                desc = f'{sub}, {extra} л/ч'
            elif sub and extra and sub.lower() not in extra.lower() and sub != name:
                desc = f'{sub}. {extra}'
            else:
                desc = extra or sub
            r = dict(name=name, desc=desc, price=price(c.get(10)), _flag=flag, _d=price(c.get(11)))
            if not r['price']:
                report['excluded_noprice'].append(f"{name} (нет РРЦ)"); continue
            if clearance(flag) and not include_clearance:
                report['excluded_clearance'].append(f"{name} ({r['price']} ₽)"); continue
            accessories.setdefault(('Hisense', acc_cat or 'Прочее'), []).append(r)
            continue
        else:
            continue
        # общая фильтрация товарных строк
        if not r['price']:
            report['excluded_noprice'].append(f"{r['model']} (нет РРЦ)"); continue
        if clearance(r.get('_flag')) and not include_clearance:
            report['excluded_clearance'].append(f"{r['model']} ({r['price']} ₽)"); continue
        t['rows'].append(r)


def hisense_features(path, pages):
    """Короткие списки особенностей серий из подробных листов (строки между заголовком серии и первой моделью)."""
    data = xr.load(path)
    mapping = {'RAC INVERTER': WALL, 'RAC ON-OFF': WALL}
    for sheet, rules in mapping.items():
        rows = data[sheet]
        order = sorted(rows)
        for i, rn in enumerate(order):
            c = rows[rn]
            if not any('УЗНАТЬ' in str(v) for v in c.values()):
                continue
            title = txt(c.get(3) or c.get(2) or '')
            sid = next((s for rx, s, _ in rules if re.search(rx, title.upper())), None)
            if not sid or sid in ('zoomw',):
                continue
            feats = []
            for rn2 in order[i + 1:]:
                c2 = rows[rn2]
                if CODE_RE.match(str(c2.get(1, ''))):
                    break
                if any('УЗНАТЬ' in str(v) for v in c2.values()):
                    break
                for col, v in sorted(c2.items()):
                    s = txt(v)
                    if col >= 6 and s and len(s) > 8 and not re.fullmatch(r'[\d.,\s]+', s) and 'ПРАЙС' not in s.upper():
                        s = s.strip('*•▪§ ').strip().replace('дб(А)', 'дБ(А)').replace('Presition', 'Precision')
                        if 'ВИДЕО' in s.upper():
                            continue
                        if s and s not in feats:
                            feats.append(s)
            sec = pages.get('hisense-nastennye', {}).get(sid)
            if sec and not sec['features']:
                sec['features'] = feats[:6]


# ---------- LG ----------
def build_lg(path, pages, accessories):
    data = xr.load(path)
    rows = data['Краткий прайс']
    series = None
    last = None
    for rn in sorted(rows):
        if rn < 7:
            continue
        c = rows[rn]
        code = txt(c.get(1))
        if code and CODE_RE.match(code):
            if series is None:
                continue
            cap = kcap(txt(c.get(2)))
            r = dict(model=txt(c.get(4)), cap=cap, cool=nominal(c.get(6)), heat=nominal(c.get(7)), eff=eff(c.get(9)),
                     noise=noise(c.get(8)), price=price(c.get(12)), _d=price(c.get(13)))
            sid, ttl = series
            sec = pages.section('lg', sid, ttl)
            t = pages.table(sec, 'main', None, 'lgkit')
            t['rows'].append(r)
            last = r
        elif 3 in c and 1 not in c and last is not None and txt(c.get(5)) == 'наружный блок':
            last['model'] = f"{last['model']} / {txt(c.get(4))}"
        elif 2 in c and len(c) == 1:
            t = txt(c[2])
            if t.upper().startswith('МУЛЬТИ'):
                break  # дальше идёт мульти-сплит: он собирается из листа PROMULTI с понятными колонками
            if t.upper() == 'СПЛИТ-СИСТЕМЫ':
                continue
            series = (re.sub(r'\W+', '', t).lower(), 'LG ' + t.replace('ARTCOOL', 'ARTCOOL'))
            last = None
    # мульти-сплит PROMULTI 2.0
    mrows = data['PROMULTI 2.0 (R32)']
    sec_out = pages.section('lg', 'promulti', 'LG ProMulti 2.0 — мульти-сплит системы (R32)')
    cur = None
    for rn in sorted(mrows):
        if rn < 5:
            continue
        c = mrows[rn]
        code = txt(c.get(1))
        if not (code and CODE_RE.match(code)):
            h = txt(c.get(2))
            if h and 1 not in c:
                low = h.lower()
                if 'наружные блоки' in low:
                    cur = ('out', 'Наружные блоки')
                elif 'внутренние блоки' in low:
                    kind = ('Кассетные однопоточные' if 'однопоточного' in low else 'Канальные' if 'канального' in low
                            else 'Настенные' if 'настенного' in low else 'Кассетные' if 'кассет' in low else 'Внутренние')
                    ser = re.search(r'серии\s*(.*)$', h, re.I)
                    cur = ('in', f'{kind}' + (f', серия {ser.group(1).strip()}' if ser and ser.group(1).strip() else ''))
            continue
        art = txt(c.get(4))
        p = price(c.get(14))
        if cur is None:
            continue
        if 2 not in c:  # аксессуар (пульт, Wi-Fi, панель)
            if p:
                accessories.setdefault(('LG', 'Принадлежности к мульти-сплит системам'), []).append(dict(name=f"{art} — {txt(c.get(6))}", desc=None, price=p, _d=price(c.get(15))))
            continue
        if cur[0] == 'out':
            n = re.search(r'на (\d) внутр', txt(c.get(5)) or '')
            r = dict(model=art, cap=kcap(txt(c.get(2))), cool=nominal(c.get(6)), heat=nominal(c.get(7)),
                     eff=eff((txt(c.get(8)) or '').split('/')[-1]), units=n.group(1) if n else None, price=p, _d=price(c.get(15)))
            t = pages.table(sec_out, 'out', 'Наружные блоки', 'lgout')
        else:
            r = dict(model=art, cap=kcap(txt(c.get(2))), cool=nominal(c.get(6)), heat=nominal(c.get(7)), price=p, _d=price(c.get(15)))
            t = pages.table(sec_out, cur[1], 'Внутренние блоки — ' + cur[1][0].lower() + cur[1][1:], 'lgin')
        if not p:
            report['excluded_noprice'].append(f'{art} (нет РРЦ)')
            continue
        t['rows'].append(r)


# ---------- ROLAND (из уже опубликованных страниц сайта) ----------
def read_roland():
    out = []
    for slug in ('favorite-ii-inverter', 'favorite-ii', 'maestro'):
        p = os.path.join(ROOT, 'content', 'projects', slug, 'index.md')
        md = open(p, encoding='utf-8').read()
        title = re.search(r'^title:\s*"(.*)"', md, re.M).group(1)
        m = re.search(r'### Модели и цены\s*\n\n((?:\|.*\n)+)', md)
        rows = []
        for line in m.group(1).splitlines()[2:]:
            cells = [x.strip() for x in line.strip().strip('|').split('|')]
            pr = int(re.sub(r'\D', '', cells[-1]))
            rows.append(dict(model=cells[0], cap=cells[1], noise=cells[2], price=pr))
        out.append(dict(page=slug, title=title, rows=rows))
    return out


# ---------- сборка ----------
def finalize(pages, osushiteli):
    out = OrderedDict()
    order = {'hisense-nastennye': list(WALL_TITLES), 'promyshlennye': SEMI_ORDER}
    for page, secs in pages.items():
        if page.startswith('_'):
            continue
        ids = [i for i in order.get(page, []) if i in secs] + [i for i in secs if i not in order.get(page, [])]
        lst = []
        for sid in ids:
            s = secs[sid]
            tables = [dict(title=t['title'], kind=t['kind'], rows=t['rows']) for t in s['tables'].values() if t['rows']]
            if tables:
                lst.append(dict(id=s['id'], title=s['title'], images=s['images'], features=s['features'], note=s['note'], tables=tables))
        out[page] = lst
    return out


# ---------- индекс серий для каталога с фильтрами (data/series.json) ----------
# Инверторность серий, у которых в таблицах нет разбивки «Инверторные / Классические»: по названиям серий в прайсах
SERIES_TECH = {'sensation': 'yes', 'vision': 'yes', 'vibe': 'yes', 'expert': 'yes',
               'deluxepro': 'yes', 'artcoolmirror': 'yes', 'procool': 'yes', 'promulti': 'yes'}
SERIES_TYPE = {'hisense-nastennye': 'wall', 'promyshlennye': 'semi', 'hisense-multi-split': 'multi',
               'hisense-mobilnye': 'mobile', 'lg': 'wall'}
SERIES_TITLE = {'kass': 'Hisense кассетные сплит-системы', 'duct': 'Hisense канальные сплит-системы',
                'floor': 'Hisense напольно-потолочные и консольные сплит-системы', 'column': 'Hisense колонные сплит-системы',
                'outdoor': 'Hisense: наружные блоки мульти-сплит', 'indoor': 'Hisense: внутренние блоки мульти-сплит'}


def _first_num(s):
    m = re.match(r'\s*(\d+(?:[.,]\d+)?)', str(s or ''))
    return float(m.group(1).replace(',', '.')) if m else None


def _series_stats(rows, eff_key='eff'):
    prices = [r['price'] for r in rows if r.get('price')]
    kws = [k for k in (_first_num(r.get('cool')) for r in rows) if k is not None]
    noises = [n for n in (_first_num(r.get('noise')) for r in rows) if n is not None]
    effs = sorted({r[eff_key].split('/')[0] for r in rows if r.get(eff_key)})
    hp = 'yes' if any(r.get('heat') for r in rows) else 'no'  # «тепловой насос»: у серии есть режим обогрева
    return dict(models=len(rows), hp=hp, priceMin=min(prices) if prices else None, priceMax=max(prices) if prices else None,
                kwMin=min(kws) if kws else None, kwMax=max(kws) if kws else None,
                noiseMin=min(noises) if noises else None, eff=effs)


def model_url(page, sid):
    """Адрес страницы модели из data/models.toml (если записи нет, прежний адрес с якорем)."""
    import tomllib
    with open(os.path.join(ROOT, 'data', 'models.toml'), 'rb') as f:
        m = tomllib.load(f).get(page, {}).get(sid)
    return f"/projects/{page}/{m['slug']}/" if m else f"/projects/{page}/#{sid}"


def build_series(cat):
    """Одна карточка = одна серия (раздел страницы каталога или страница Roland). Все данные берутся из catalog.json."""
    out = []

    def tech_of(sid, tables):
        if sid in SERIES_TECH:
            return SERIES_TECH[sid]
        t = ' '.join((x.get('title') or '') for x in tables).lower()
        inv = 'инвертор' in t or 'inverter' in t
        cls = 'классическ' in t or 'on/off' in t
        return 'both' if inv and cls else 'yes' if inv else 'no' if cls else ''

    for r in cat['roland']:
        rows = [dict(price=x['price'], cool=x['cap'], heat=('1' if '/' in x['cap'] else None), noise=x['noise'], eff='A') for x in r['rows']]
        out.append(dict(id='roland-' + r['page'], title=r['title'], brand='Roland', type='wall',
                        tech='yes' if r['page'] == 'favorite-ii-inverter' else 'no', url=f"/projects/{r['page']}/",
                        page=r['page'], image=dict(page=r['page'], file='photo.png'), **_series_stats(rows)))
    order = ['hisense-nastennye', 'promyshlennye', 'hisense-multi-split', 'hisense-mobilnye', 'lg']
    for page in order:
        for s in cat['pages'].get(page, []):
            rows = [x for t in s['tables'] for x in t['rows']]
            typ = 'multi' if s['id'] == 'promulti' else SERIES_TYPE[page]
            title = SERIES_TITLE.get(s['id'], s['title'])
            if page == 'hisense-mobilnye':
                title = 'Hisense ' + s['title'][0].lower() + s['title'][1:]
            img = s['images'][0]['file'] if s.get('images') else None
            out.append(dict(id=f"{page}-{s['id']}", title=title, brand='LG' if page == 'lg' else 'Hisense', type=typ,
                            tech=tech_of(s['id'], s['tables']), url=model_url(page, s['id']), page=page,
                            image=dict(page=page, file=img) if img else None, **_series_stats(rows)))
    dh = cat.get('osushiteli') or []
    if dh:
        out.append(dict(id='hisense-osushiteli', title='Hisense Air Go Pro (осушитель)', brand='Hisense', type='dehum', tech='',
                        url='/projects/osushiteli/', page='osushiteli', image=None, models=len(dh), hp='',
                        priceMin=min(x['price'] for x in dh), priceMax=max(x['price'] for x in dh),
                        kwMin=None, kwMax=None, noiseMin=None, eff=[]))
    out.append(dict(id='ventilyaciya', title='Вентиляция', brand='', type='vent', tech='', url='/projects/ventilyaciya/',
                    page='ventilyaciya', image=None, models=0, hp='', priceMin=None, priceMax=None, kwMin=None, kwMax=None,
                    noiseMin=None, eff=[]))
    return out


def strip_private(o):
    if isinstance(o, dict):
        return {k: strip_private(v) for k, v in o.items() if not k.startswith('_') and v is not None}
    if isinstance(o, list):
        return [strip_private(x) for x in o]
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hisense', required=True)
    ap.add_argument('--lg', required=True)
    ap.add_argument('--photos', action='store_true')
    ap.add_argument('--include-clearance', action='store_true')
    a = ap.parse_args()

    pages = Pages()
    accessories = OrderedDict()
    build_hisense(a.hisense, pages, accessories, a.include_clearance)
    hisense_features(a.hisense, pages)
    build_lg(a.lg, pages, accessories)
    osush = pages.pop('_osushiteli', [])
    finalized = finalize(pages, osush)

    if a.photos:
        import photos
        photos.export(a.hisense, a.lg, finalized)

    cat = OrderedDict(priceDate=PRICE_DATE, pages=finalized,
                      osushiteli=[r for r in osush if r['price'] and not clearance(r.get('_flag'))],
                      accessories=[dict(brand=b, category=c, rows=r) for (b, c), r in accessories.items()],
                      roland=read_roland())
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    with open(os.path.join(ROOT, 'data', 'catalog.json'), 'w', encoding='utf-8') as f:
        json.dump(strip_private(cat), f, ensure_ascii=False, indent=1)
    series = build_series(strip_private(cat))
    with open(os.path.join(ROOT, 'data', 'series.json'), 'w', encoding='utf-8') as f:
        json.dump(strip_private(series), f, ensure_ascii=False, indent=1)
    print(f'Серий в каталоге с фильтрами: {len(series)}')

    n = sum(len(t['rows']) for secs in finalized.values() for s in secs for t in s['tables'])
    print(f'Позиции на страницах: {n}; аксессуары: {sum(len(x) for x in accessories.values())}; осушители: {len(osush)}')
    for page, secs in finalized.items():
        print(f'  {page}: ' + ', '.join(f"{s['title']}[{sum(len(t['rows']) for t in s['tables'])}]" for s in secs))
    print(f"Исключено как «распродажа/ликвидация остатков»: {len(report['excluded_clearance'])}")
    for x in report['excluded_clearance']:
        print('   -', x)
    print('Исключено без РРЦ:', report['excluded_noprice'])
    print('Заметки:', report['notes'])


if __name__ == '__main__':
    main()
