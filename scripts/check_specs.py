"""Проверка data/specs и static/docs: все ссылки на PDF ведут на существующие файлы, лишних файлов нет, размеры совпадают с записанными."""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
used, bad = {}, 0
for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'specs', '*.yaml'))):
    txt = open(f, encoding='utf-8').read()
    for m in re.finditer(r'file: "(/docs/[^"]+)"\s+size: (\d+)', txt):
        used[m.group(1)] = int(m.group(2))
        p = os.path.join(ROOT, 'static', m.group(1).lstrip('/'))
        if not os.path.exists(p):
            print('НЕТ ФАЙЛА', os.path.basename(f), m.group(1)); bad += 1
        elif os.path.getsize(p) != int(m.group(2)):
            print('РАЗМЕР НЕ СОВПАДАЕТ', m.group(1)); bad += 1
files = [os.path.relpath(os.path.join(dp, x), os.path.join(ROOT, 'static')).replace(os.sep, '/') for dp, _, fs in os.walk(os.path.join(ROOT, 'static', 'docs')) for x in fs]
extra = [e for e in files if '/' + e not in used]
print(f'ссылок на PDF: {len(used)}, файлов: {len(files)}, ошибок: {bad}, лишних файлов: {len(extra)}')
for e in extra:
    print('  лишний:', e)
sys.exit(1 if bad else 0)
