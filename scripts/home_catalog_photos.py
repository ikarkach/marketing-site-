"""Фото для карточек блока «Каталог» на главной (data/home-catalog.yaml).

Берёт уже имеющиеся фото моделей, обрезает белые поля, вписывает в одинаковое полотно
(белый фон, товар по центру и прижат к низу) и сохраняет WebP в двух размерах: 1x и 2x.

    python scripts/home_catalog_photos.py
"""
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "static/images/models"
OUT = ROOT / "static/images/home"

# имя карточки -> исходное фото
PHOTOS = {
    "wall": "roland/favorite-ii-inverter/02.webp",
    "multi": "lg/promulti-2-0/01.webp",
    "semi": "hisense/kassetnye/01.webp",
    "mobile": "hisense/seriya-v/01.webp",
    "vent": "royal-clima/brezza-rcb-150-lux/02.webp",
    "dry": "royal-clima/carisma-villa/02.webp",
}

W, H = 200, 160      # размер 1x (в CSS); 2x — вдвое больше
FILL = 0.9           # товар занимает не больше 90 % ширины/высоты полотна


def trim(im: Image.Image) -> Image.Image:
    rgb = im.convert("RGBA")
    flat = Image.new("RGB", rgb.size, "white")
    flat.paste(rgb, mask=rgb.split()[3])
    diff = ImageChops.difference(flat, Image.new("RGB", flat.size, "white")).convert("L")
    box = diff.point(lambda p: 255 if p > 12 else 0).getbbox()
    return flat.crop(box) if box else flat


def render(im: Image.Image, scale: int) -> Image.Image:
    cw, ch = W * scale, H * scale
    k = min(cw * FILL / im.width, ch * FILL / im.height)
    item = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    canvas = Image.new("RGB", (cw, ch), "white")
    canvas.paste(item, ((cw - item.width) // 2, ch - item.height))
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rel in PHOTOS.items():
        im = trim(Image.open(SRC / rel))
        for scale, suffix in ((1, ""), (2, "@2x")):
            path = OUT / f"cat-{name}{suffix}.webp"
            render(im, scale).save(path, "WEBP", quality=80, method=6)
            print(path.relative_to(ROOT), path.stat().st_size // 1024, "КБ")


if __name__ == "__main__":
    main()
