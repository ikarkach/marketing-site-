"""Минимальное чтение xlsx без внешних библиотек (только стандартная библиотека Python)."""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def _col(ref):
    n = 0
    for ch in re.match(r'[A-Z]+', ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n


def load(path):
    """Возвращает {имя листа: {номер строки: {номер столбца: значение}}}. Пустые ячейки пропускаются."""
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS):
            shared.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    out = {}
    for s in wb.find('m:sheets', NS):
        target = rels[s.get('{%s}id' % NS['r'])].lstrip('/')
        if not target.startswith('xl/'):
            target = 'xl/' + target
        rows = {}
        for row in ET.fromstring(z.read(target)).iter('{%s}row' % NS['m']):
            cells = {}
            for c in row.findall('m:c', NS):
                v = c.find('m:v', NS)
                kind = c.get('t')
                if kind == 's' and v is not None:
                    val = shared[int(v.text)]
                elif kind == 'inlineStr':
                    val = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
                else:
                    val = v.text if v is not None else None
                if val not in (None, ''):
                    cells[_col(c.get('r'))] = val
            if cells:
                rows[int(row.get('r'))] = cells
        out[s.get('name')] = rows
    return out
