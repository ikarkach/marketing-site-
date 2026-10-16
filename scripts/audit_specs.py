"""Поиск подозрительных значений в data/specs/*.yaml (ничего не исправляет, только печатает для отчёта):
несовпадение диаметров труб в мм и в дюймах, длина трассы меньше номинальной, минимальная больше максимальной."""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCH = {'6.35': '1/4', '9.52': '3/8', '9.53': '3/8', '12.7': '1/2', '15.88': '5/8', '15.9': '5/8', '19.05': '3/4', '19.1': '3/4', '22.2': '7/8', '25.4': '1'}


def num(s):
    m = re.match(r'-?\d+(?:[.,]\d+)?', s.strip().replace('\\"', '"'))
    return float(m.group().replace(',', '.')) if m else None


def parse(path):
    txt = open(path, encoding='utf-8').read().split('\ndocs:')[0]
    out = []
    for tb in re.split(r'\n  - title:', txt)[1:]:
        models = re.findall(r'"((?:[^"\\]|\\.)*)"', re.search(r'models: \[(.*?)\]', tb).group(1))
        rows = {}
        for m in re.finditer(r'- label: "((?:[^"\\]|\\.)*)"\n\s+values: \[(.*?)\]\n', tb):
            rows.setdefault(m.group(1), re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2)))
        out.append((models, rows))
    return out


n = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'specs', '*.yaml'))):
    name = os.path.basename(f)[:-5]
    for models, rows in parse(f):
        for kind in ('жидкостной', 'газовой'):
            mm = next((v for l, v in rows.items() if l.startswith(f'Диаметр {kind} трубы, мм')), None)
            inch = next((v for l, v in rows.items() if l.startswith(f'Диаметр {kind} трубы, дюйм')), None)
            if mm and inch:
                for i, m in enumerate(models):
                    a = num(mm[i]) if i < len(mm) else None
                    fr = re.match(r'\d+(?:/\d+)?', (inch[i] or '').strip()) if i < len(inch) else None   # «1/4" x4» (по числу ветвей): берём дробь
                    b = fr.group() if fr else ''
                    if a is not None and b and INCH.get(f'{a:g}') != b:
                        print(f'{name} | {m}: диаметр {kind} трубы {mm[i]} мм, но в дюймах «{inch[i]}»'); n += 1
        mx = next((v for l, v in rows.items() if l.startswith('Максимальная длина трассы')), None)
        mn = next((v for l, v in rows.items() if l.startswith('Минимальная длина трассы')), None)
        nom = next((v for l, v in rows.items() if l.startswith('Номинальная длина трассы')), None)
        for i, m in enumerate(models):
            a = num(mx[i]) if mx and i < len(mx) and mx[i] else None
            b = num(mn[i]) if mn and i < len(mn) and mn[i] else None
            c = num(nom[i]) if nom and i < len(nom) and nom[i] else None
            if a is not None and c is not None and c > a:
                print(f'{name} | {m}: номинальная длина трассы {c:g} больше максимальной {a:g}'); n += 1
            if a is not None and b is not None and b > a:
                print(f'{name} | {m}: минимальная длина трассы {b:g} больше максимальной {a:g}'); n += 1
print('подозрительных значений:', n)
