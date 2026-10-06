"""Чистит логотип Usplit: исходник static/logo.src.png (807x331) — мягкий, с шумом сжатия.
Логотип одноцветный, форму задаёт прозрачность: увеличиваем маску, делаем границу резкой и возвращаем нужный размер со сглаживанием.
Результат: static/logo.png (для главной, 1200 px) и static/logo-header.png (для шапки, 2x от 112x44).
Запуск:  python scripts/sharpen_logo.py   (нужен Pillow)
"""
import os
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'static', 'logo.src.png')
COLOR = (3, 95, 181)  # единственный цвет логотипа
WORK = 4              # во сколько раз увеличиваем для обработки


def build(out_w, out_path, steep=5.0, mid=0.36):
    src = Image.open(SRC).convert('RGBA')
    a = src.getchannel('A')
    big = a.resize((a.width * WORK, a.height * WORK), Image.BICUBIC).filter(ImageFilter.GaussianBlur(WORK * 0.35))
    lut = [round(255 * min(1.0, max(0.0, (v / 255 - mid) * steep + 0.5))) for v in range(256)]  # резкая граница
    big = big.point(lut)
    h = round(out_w * src.height / src.width)
    alpha = big.resize((out_w, h), Image.LANCZOS)        # сглаживание краёв при уменьшении
    rgba = Image.new('RGBA', (out_w, h), COLOR + (0,))
    rgba.putalpha(alpha)
    rgba.save(out_path, optimize=True)
    print(out_path, rgba.size, os.path.getsize(out_path) // 1024, 'КБ')


if __name__ == '__main__':
    build(1200, os.path.join(ROOT, 'static', 'logo.png'))
    build(260, os.path.join(ROOT, 'static', 'logo-header.png'))
