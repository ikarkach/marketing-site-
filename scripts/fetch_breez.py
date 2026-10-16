"""Технические характеристики и документация серии из каталога breez.ru -> data/specs/*.yaml и static/docs/.

Что делает (только общедоступные страницы, личный кабинет не используется):
  1. скачивает XLS-выгрузку характеристик страницы серии (адрес + ?download_as_xls);
  2. оставляет только наши модели (--models), в нашем порядке; группы и порядок строк как на Бризе, модели столбцами;
  3. чистит значения: пустые, «—», «( - )» не выводятся, строка, пустая у всех моделей, удаляется; «5?1,5» -> «5×1,5»;
  4. скачивает PDF из блока «Документация» в static/docs/<бренд>/<папка>/ и пишет название и размер в YAML.
Описания серий с Бриза не берутся (дубль контента): только цифры характеристик и PDF.

Одна серия:
  python scripts/fetch_breez.py https://breez.ru/products/classic-favorite-2-2024/ --brand roland --folder favorite-ii \
      --out roland-favorite-ii --models "FU-07HSS010/N6,FU-09HSS010/N6" --docname roland-favorite-ii-2024
Несколько серий на одной странице сайта (каждая серия = отдельная таблица) или цвета в одной таблице (--merge):
  см. scripts/build_specs.py (там сопоставление «страница сайта -> серии Бриза»).
Без сторонних библиотек. Сеть через curl (Python-запросы с этой машины нестабильны).
"""
import argparse
import html
import os
import re
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get('BREEZ_CACHE') or os.path.join(os.environ.get('TEMP', '.'), 'breez_specs_cache')
UA = 'Mozilla/5.0 (compatible; Usplit catalog build)'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
EMPTY = {'', '-', '—', '–', '( - )', '(-)', '- ( - )', '— ( - )', 'нет данных', 'н/д'}


def curl(url, dst, minsize=1000):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for _ in range(5):
        r = subprocess.run(['curl', '-s', '-f', '--max-time', '120', '-A', UA, '-o', dst, url])
        if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > minsize:
            return True
    return False


# ---------- чтение .xlsx без библиотек ----------
def _col(ref):
    n = 0
    for ch in re.match(r'[A-Z]+', ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS):
            shared.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheet = wb.find('m:sheets', NS)[0]
    target = rels[sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')].lstrip('/')
    root = ET.fromstring(z.read(target if target.startswith('xl/') else 'xl/' + target))
    rows = []
    for row in root.iter('{%s}row' % NS['m']):
        cells = {}
        for c in row.findall('m:c', NS):
            v = c.find('m:v', NS)
            t = c.get('t')
            if t == 's' and v is not None:
                val = shared[int(v.text)]
            elif t == 'inlineStr':
                val = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
            else:
                val = v.text if v is not None else None
            if val is not None:
                cells[_col(c.get('r'))] = val
        rows.append([cells.get(i) for i in range(max(cells) + 1)] if cells else [])
    return rows


# ---------- очистка значений ----------
def clean_label(s):
    s = html.unescape(html.unescape(s or ''))
    s = re.sub(r'<sup>\s*2\s*</sup>', '²', s)
    s = re.sub(r'<sup>\s*3\s*</sup>', '³', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def clean_value(s):
    if s is None:
        return ''
    v = clean_label(str(s))
    v = re.sub(r'\s*\(\s*-\s*\)\s*$', '', v)          # «2.23 ( - )» -> «2.23»
    v = re.sub(r'(?<=\d)\?(?=\d)', '×', v)             # битый символ: «5?1,5» -> «5×1,5»
    if re.fullmatch(r'[\d.,]+(?:\s*[x*×хХ]\s*[\d.,]+)+', v):     # «715x285x194», «430*231» -> «715×285×194», «430×231»
        v = re.sub(r'\s*[x*×хХ]\s*', '×', v)
    if v in EMPTY:
        return ''
    if re.fullmatch(r'-?\d+\.\d+', v):                 # десятичная точка -> запятая (цифры те же)
        v = v.replace('.', ',')
    return v


def norm(s):
    return re.sub(r'\s+', '', (s or '').upper())


# ---------- разбор таблицы выгрузки ----------
def parse_specs(rows):
    """-> (модели по порядку, [ {name, rows:[(label, {модель: значение})]} ])"""
    start = next((i for i, r in enumerate(rows) if r and (r[0] or '').strip() == 'Технические характеристики'), None)
    if start is None:
        raise RuntimeError('в выгрузке нет блока «Технические характеристики»')
    groups, cur, models, i = [], None, [], start + 1
    while i < len(rows):
        r = rows[i]
        nz = [c for c in r if c not in (None, '')]
        nxt = rows[i + 1] if i + 1 < len(rows) else []
        if len(nz) == 1 and r and r[0] and nxt and nxt[0] in (None, ''):
            cur = {'name': clean_label(r[0]), 'rows': []}
            groups.append(cur)
            hdr = [clean_label(x) for x in nxt[1:]]
            if not models:
                models = [h for h in hdr if h]
            cur['hdr'] = hdr
            i += 2
            continue
        if cur is not None and r and r[0]:
            vals = {}
            for h, v in zip(cur['hdr'], r[1:]):
                if h:
                    vals[h] = clean_value(v)
            cur['rows'].append((clean_label(r[0]), vals))
        i += 1
    return models, groups


def match_models(wanted, models):
    """Наш артикул -> столбец Бриза (точное совпадение без пробелов; «(B)» и «(S)» сохраняются)."""
    by = {norm(m): m for m in models}
    out = {}
    for w in wanted:
        toks = [norm(t) for t in re.split(r'\s*[+/]\s*', w) if t.strip()]
        for cand in [norm(w)] + toks:
            if cand in by:
                out[w] = by[cand]
                break
    return out


def build_table(series_url, wanted, xlsx_path):
    models, groups = parse_specs(read_xlsx(xlsx_path))
    pick = match_models(wanted, models) if wanted else {m: m for m in models}
    ours = [w for w in (wanted or models) if w in pick]
    out = []
    for g in groups:
        rows = []
        for label, vals in g['rows']:
            row = [vals.get(pick[w], '') for w in ours]
            if any(row):
                rows.append({'label': label, 'values': row})
        if rows:
            out.append({'name': g['name'], 'rows': rows})
    missing = [w for w in (wanted or []) if w not in pick]
    return ours, out, missing


def merge_tables(parts):
    """Цвета одной серии в одну таблицу: объединяем модели, строки по порядку первого появления."""
    models, groups = [], []
    for ms, gs in parts:
        base = len(models)
        models += ms
        for g in gs:
            tg = next((x for x in groups if x['name'] == g['name']), None)
            if tg is None:
                tg = {'name': g['name'], 'rows': []}
                groups.append(tg)
            for r in g['rows']:
                tr = next((x for x in tg['rows'] if x['label'] == r['label']), None)
                if tr is None:
                    tr = {'label': r['label'], 'values': [''] * base}
                    tg['rows'].append(tr)
                tr['values'] += [''] * (base - len(tr['values']))
                tr['values'] += r['values']
    for g in groups:
        for r in g['rows']:
            r['values'] += [''] * (len(models) - len(r['values']))
    return models, groups


# ---------- документы ----------
def find_docs(series_url, cache_html):
    if not (os.path.exists(cache_html) and os.path.getsize(cache_html) > 5000):
        if not curl(series_url, cache_html, 5000):
            raise RuntimeError('не открылась страница серии ' + series_url)
    t = open(cache_html, encoding='utf-8').read()
    docs, seen = [], set()
    for u, txt in re.findall(r'href="(https://docs\.breez\.ru/[^"]+\.pdf)"[^>]*>(.*?)</a>', t, re.S):
        if u in seen:
            continue
        seen.add(u)
        title = clean_label(re.sub(r'Загрузка\.*', '', txt))
        docs.append((u, title))
    return docs


def doc_kind(url):
    low = url.lower()
    if 'info-list' in low or 'buklet' in low:
        return 'buklet', 'Буклет'
    if 'instruction' in low or 'instr' in low:
        return 'instrukciya', 'Инструкция'
    return 'dokument', 'Документ'


# ---------- YAML без библиотек ----------
def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def dump_yaml(d):
    L = []
    L.append('# Создано scripts/fetch_breez.py из общедоступной выгрузки каталога breez.ru. Руками не править: перезапишется.')
    L.append(f'brand: {q(d["brand"])}')
    L.append('tables:')
    for t in d['tables']:
        L.append(f'  - title: {q(t["title"])}')
        L.append(f'    source: {q(t["source"])}')
        L.append('    models: [' + ', '.join(q(m) for m in t['models']) + ']')
        L.append('    groups:')
        for g in t['groups']:
            L.append(f'      - name: {q(g["name"])}')
            L.append('        rows:')
            for r in g['rows']:
                L.append(f'          - label: {q(r["label"])}')
                L.append('            values: [' + ', '.join(q(v) for v in r['values']) + ']')
    L.append('docs:' if d['docs'] else 'docs: []')
    for x in d['docs']:
        L.append(f'  - title: {q(x["title"])}')
        L.append(f'    file: {q(x["file"])}')
        L.append(f'    size: {x["size"]}')
        L.append(f'    kind: {q(x["kind"])}')
    return '\n'.join(L) + '\n'


# ---------- основной сценарий ----------
def fetch_series(url, wanted):
    slug = url.rstrip('/').split('/')[-1]
    xlsx = os.path.join(CACHE, slug + '.xlsx')
    if not (os.path.exists(xlsx) and os.path.getsize(xlsx) > 3000):
        if not curl(url.rstrip('/') + '/?download_as_xls', xlsx, 3000):
            raise RuntimeError('не скачалась выгрузка ' + url)
    return build_table(url, wanted, xlsx)


def download_docs(urls_titles, brand, folder, docname, max_mb=15):
    """Скачивает PDF, возвращает список {title,file,size,kind}. Файлы больше max_mb не сохраняет, а сообщает."""
    out, big = [], []
    dst_dir = os.path.join(ROOT, 'static', 'docs', brand, folder)
    for url, title in urls_titles:
        kind, word = doc_kind(url)
        slug = url.rsplit('/', 1)[-1]
        name = f'{docname(url)}-{kind}.pdf'
        dst = os.path.join(dst_dir, name)
        tmp = os.path.join(CACHE, 'pdf', slug)
        if not (os.path.exists(tmp) and os.path.getsize(tmp) > 1000):
            if not curl(url, tmp, 1000):
                print('  НЕ СКАЧАН PDF', url)
                continue
        size = os.path.getsize(tmp)
        if size > max_mb * 1024 * 1024:
            big.append((url, size))
            continue
        os.makedirs(dst_dir, exist_ok=True)
        with open(tmp, 'rb') as a, open(dst, 'wb') as b:
            b.write(a.read())
        out.append({'title': title or word, 'file': f'/docs/{brand}/{folder}/{name}', 'size': size, 'kind': kind})
    return out, big


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('url')
    ap.add_argument('--brand', required=True, help='папка бренда: roland, hisense, lg, royal-clima')
    ap.add_argument('--folder', required=True, help='папка серии в static/docs/<бренд>/')
    ap.add_argument('--out', required=True, help='имя файла data/specs/<out>.yaml')
    ap.add_argument('--models', default='', help='наши артикулы через запятую (пусто = все модели серии)')
    ap.add_argument('--docname', default='', help='префикс имён PDF')
    ap.add_argument('--title', default='')
    a = ap.parse_args()
    wanted = [m.strip() for m in a.models.split(',') if m.strip()]
    models, groups, missing = fetch_series(a.url, wanted)
    prefix = a.docname or f'{a.brand}-{a.url.rstrip("/").split("/")[-1]}'
    docs_found = find_docs(a.url, os.path.join(CACHE, a.url.rstrip('/').split('/')[-1] + '.html'))
    docs, big = download_docs(docs_found, a.brand, a.folder, lambda u: prefix)
    d = {'brand': a.brand, 'tables': [{'title': a.title, 'source': a.url, 'models': models, 'groups': groups}], 'docs': docs}
    dst = os.path.join(ROOT, 'data', 'specs', a.out + '.yaml')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w', encoding='utf-8', newline='\n').write(dump_yaml(d))
    print(f'{a.out}: моделей {len(models)}, групп {len(groups)}, строк {sum(len(g["rows"]) for g in groups)}, PDF {len(docs)}')
    if missing:
        print('  нет на Бризе:', ', '.join(missing))
    for u, s in big:
        print(f'  PDF больше 15 МБ не сохранён: {u} ({s / 1048576:.1f} МБ)')


if __name__ == '__main__':
    main()
