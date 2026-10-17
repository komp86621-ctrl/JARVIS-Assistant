# make_icon.py — создаёт icon.ico с арк-реактором
from PIL import Image, ImageDraw, ImageFilter
import math, os

def make_icon(path="icon.ico", size=256):
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = S // 2, S // 2

    # ФОН — тёмный круг
    bg_r = int(S * 0.48)
    draw.ellipse([cx - bg_r, cy - bg_r, cx + bg_r, cy + bg_r],
                 fill=(10, 15, 25, 255))

    # Свечение вокруг
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    glow_r = int(S * 0.45)
    gdraw.ellipse([cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
                  fill=(0, 200, 255, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(int(S * 0.04)))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # ВНЕШНЕЕ КОЛЬЦО (cyan)
    r1 = int(S * 0.42)
    width1 = max(2, int(S * 0.012))
    for i in range(0, 360, 90):
        draw.arc([cx - r1, cy - r1, cx + r1, cy + r1],
                 start=i, end=i + 70,
                 fill=(0, 255, 255, 255), width=width1)

    # СРЕДНЕЕ КОЛЬЦО (blue)
    r2 = int(S * 0.33)
    width2 = max(2, int(S * 0.010))
    for i in range(15, 360, 120):
        draw.arc([cx - r2, cy - r2, cx + r2, cy + r2],
                 start=i, end=i + 60,
                 fill=(0, 140, 255, 255), width=width2)

    # ВНУТРЕННЕЕ КОЛЬЦО
    r3 = int(S * 0.24)
    draw.ellipse([cx - r3, cy - r3, cx + r3, cy + r3],
                 outline=(0, 200, 200, 180), width=max(1, int(S * 0.005)))

    # ЯДРО — свечение
    core_r = int(S * 0.17)
    core_glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cg = ImageDraw.Draw(core_glow)
    cg.ellipse([cx - core_r, cy - core_r, cx + core_r, cy + core_r],
               fill=(255, 0, 255, 180))
    core_glow = core_glow.filter(ImageFilter.GaussianBlur(int(S * 0.03)))
    img = Image.alpha_composite(img, core_glow)
    draw = ImageDraw.Draw(img)

    # ЯДРО — градиент
    for i in range(core_r, 0, -1):
        t = i / core_r
        r = int(255 * (1 - t) + 100 * t)
        g = int(255 * (1 - t) + 0 * t)
        b = int(255 * (1 - t) + 180 * t)
        draw.ellipse([cx - i, cy - i, cx + i, cy + i],
                     fill=(r, g, b, 255))

    # ЯДРО — белый центр
    white_r = int(core_r * 0.35)
    draw.ellipse([cx - white_r, cy - white_r, cx + white_r, cy + white_r],
                 fill=(255, 255, 255, 255))

    # Уменьшаем
    img = img.resize((size, size), Image.LANCZOS)

    # Сохраняем ICO
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(path, format='ICO', sizes=sizes)
    print(f"✓ Иконка создана: {path}")
    print(f"  Размеры: {sizes}")
    print(f"  Файл: {os.path.abspath(path)}")
    print(f"  Вес: {os.path.getsize(path) / 1024:.1f} КБ")


if __name__ == "__main__":
    make_icon("icon.ico", 256)
