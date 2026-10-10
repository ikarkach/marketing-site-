"""Урезает шрифты Font Awesome до иконок, которые реально используются на сайте.

Полные шрифты темы весят ~250 КБ (fa-solid-900 + fa-brands-400), на сайте нужно около десятка иконок.
Скрипт читает коды иконок из assets/sass/_fontawesome-import.sass (строки content: "\\fXXX"),
оставляет в шрифтах только эти символы и сохраняет static/fonts/icons/fa-solid-<хеш>.woff2 и fa-brands-<хеш>.woff2.
Хеш в имени меняется вместе с набором иконок, поэтому файлы можно кешировать на год.
Имена файлов в _fontawesome-import.sass скрипт обновляет сам.

Добавить иконку: допишите её код в _fontawesome-import.sass и запустите
    python scripts/subset_icons.py
(нужны пакеты: pip install fonttools brotli)
"""
import hashlib
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
SASS = ROOT / "assets/sass/_fontawesome-import.sass"
SRC = ROOT / "themes/introduction/static/fonts/fontawesome-free/webfonts"
OUT = ROOT / "static/fonts/icons"
FONTS = {"solid": "fa-solid-900.ttf", "brands": "fa-brands-400.ttf"}


def main() -> None:
    sass = SASS.read_text(encoding="utf-8")
    codes = sorted({int(c, 16) for c in re.findall(r'content:\s*"\\([0-9a-fA-F]{4,5})"', sass)})
    if not codes:
        raise SystemExit("В _fontawesome-import.sass не найдено ни одного кода иконки")
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("fa-*.woff2"):
        old.unlink()
    for kind, name in FONTS.items():
        font = TTFont(SRC / name, recalcTimestamp=False)
        cmap = font.getBestCmap()
        present = [c for c in codes if c in cmap]
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=present)
        sub.subset(font)
        tmp = OUT / f"fa-{kind}.tmp"
        font.flavor = "woff2"
        font.save(tmp)
        digest = hashlib.sha256(tmp.read_bytes()).hexdigest()[:10]
        target = OUT / f"fa-{kind}-{digest}.woff2"
        tmp.replace(target)
        sass = re.sub(rf'url\("[^"]*fa-{kind}[^"]*"\)', f'url("/fonts/icons/{target.name}")', sass)
        print(f"{target.relative_to(ROOT)}: {len(present)} иконок, {target.stat().st_size} байт")
    SASS.write_text(sass, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
