"""Облегчает шрифты Montserrat и Roboto: оставляет только нужные начертания и символы.

1. Диапазон толщин: файлы переменные (wght 100–900), сайт использует Roboto 400–600 и Montserrat 500–600
   (см. @font-face в layouts/partials/head/fonts.html). Остальные толщины удаляются.
2. Латинские файлы урезаются до ASCII, Latin-1 и типографских знаков, которые встречаются на страницах
   (— « » × ° ² ³ → и т. п.). Кириллические файлы сохраняют все свои символы.

Оригиналы — assets/fonts-src/ (на сайт не попадают), результат — static/fonts/ (имена прежние).
Если в @font-face поменяется диапазон толщин, поправьте WEIGHTS и запустите заново:

    python scripts/subset_text_fonts.py
(нужны пакеты: pip install fonttools brotli)
"""
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/fonts-src"
OUT = ROOT / "static/fonts"

WEIGHTS = {"roboto": (400, 600), "montserrat": (500, 600)}

# ASCII + весь Latin-1 (запас для редких букв) + типографские знаки
LATIN = (
    list(range(0x20, 0x7F)) + list(range(0xA0, 0x100))
    + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x201E, 0x2026, 0x2116, 0x2122,
       0x20AC, 0x2190, 0x2192, 0x2212, 0x2264, 0x2265, 0x2103]
)


def main() -> None:
    for family, (lo, hi) in WEIGHTS.items():
        for script in ("latin", "cyrillic"):
            name = f"{family}-{script}.woff2"
            font = TTFont(SRC / name, recalcTimestamp=False)
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["*"]
            opts.name_IDs = ["*"]
            opts.notdef_outline = True
            sub = subset.Subsetter(opts)
            if script == "latin":
                sub.populate(unicodes=LATIN)
            else:
                sub.populate(unicodes=font.getBestCmap().keys())
            sub.subset(font)
            font = instancer.instantiateVariableFont(font, {"wght": (lo, hi)})
            font.flavor = "woff2"
            font.save(OUT / name)
            print(f"{name}: {(SRC / name).stat().st_size} -> {(OUT / name).stat().st_size} байт")


if __name__ == "__main__":
    main()
