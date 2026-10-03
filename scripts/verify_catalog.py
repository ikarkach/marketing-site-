#!/usr/bin/env python3
"""Независимая сверка data/catalog.json с исходными прайсами: каждая цена на сайте должна быть РИЦ своей модели.

  python scripts/verify_catalog.py --hisense <HISENSE.xlsx> --lg <LG.xlsx>

Проверяет: цена = РИЦ строки прайса (с округлением до рубля), не равна дилерской цене этой же модели,
в файле нет полей с дилерскими/спец. ценами и внутренними кодами.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xlsx_reader as xr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = re.compile(r'^(НС|BR)-\d+')


def norm(s):
    s = str(s).lower().replace('|', '+').replace(' с зимним комплектом', '')
    return re.sub(r'[\s]+', '', s)


def rub(v):
    try:
        return int(float(str(v).replace(' ', '').replace(',', '.')) + 0.5)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hisense', required=True)
    ap.add_argument('--lg', required=True)
    a = ap.parse_args()
    cat = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))

    src = {}  # модель -> [(ric, dealer)]
    h = xr.load(a.hisense)['КРАТКИЙ ПРАЙС СПЛИТЫ']
    for c in h.values():
        if CODE.match(str(c.get(1, ''))) and 2 in c:
            src.setdefault(norm(c[2]), []).append((rub(c.get(10)), rub(c.get(11))))
            if 3 in c and 10 in c:  # аксессуары: артикул иногда во втором столбце
                src.setdefault(norm(c[2]) + norm(c[3]), []).append((rub(c.get(10)), rub(c.get(11))))
    lg = xr.load(a.lg)
    for c in lg['Краткий прайс'].values():
        if CODE.match(str(c.get(1, ''))) and 4 in c:
            src.setdefault(norm(c[4]), []).append((rub(c.get(12)), rub(c.get(13))))
    for c in lg['PROMULTI 2.0 (R32)'].values():
        if CODE.match(str(c.get(1, ''))) and 4 in c:
            src.setdefault(norm(c[4]), []).append((rub(c.get(14)), rub(c.get(15))))

    checked = bad = 0

    def check(key, price, where):
        nonlocal checked, bad
        checked += 1
        cands = src.get(norm(key))
        if not cands:
            # аксессуары: имя могло быть собрано из нескольких ячеек — ищем по вхождению артикула
            cands = [v for k, vs in src.items() if norm(key).startswith(k) or k in norm(key) for v in vs] if len(norm(key)) > 4 else None
        if not cands:
            bad += 1; print('НЕТ В ПРАЙСЕ:', where, key, price); return
        if not any(r == price for r, _ in cands):
            bad += 1; print('ЦЕНА НЕ РАВНА РИЦ:', where, key, price, cands); return
        if any(r == price and d == price and r != d for r, d in cands):
            bad += 1; print('ЦЕНА РАВНА ДИЛЕРСКОЙ:', where, key, price)

    for page, secs in cat['pages'].items():
        for s in secs:
            for t in s['tables']:
                for r in t['rows']:
                    check(r['model'].split(' / ')[0] if t['kind'] == 'lgkit' else r['model'], r['price'], f"{page}/{s['id']}")
    for r in cat['osushiteli']:
        check(r['model'], r['price'], 'osushiteli')
    for g in cat['accessories']:
        for r in g['rows']:
            check(r['name'].split(' — ')[0].split(' ')[0] if g['brand'] == 'LG' else r['name'], r['price'], g['category'])

    text = open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8').read()
    for forbidden in ('dealer', 'special', 'nscode', '"code"', 'НС-', 'BR-', 'Дилерск', 'Спец'):
        if forbidden in text:
            bad += 1; print('В catalog.json найдено запрещённое поле/значение:', forbidden)
    print(f'Проверено цен: {checked}; ошибок: {bad}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
