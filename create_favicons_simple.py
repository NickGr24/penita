#!/usr/bin/env python3
"""
Простой скрипт для создания фавиконов без cairosvg
Создает базовые PNG фавиконы с буквой P
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_IMG = BASE_DIR / "main/static/img"

# Цвета в стиле юридического сайта
BG_COLOR = (26, 26, 46)  # Темно-синий
PEN_COLOR = (196, 169, 98)  # Золотой
TEXT_COLOR = (255, 255, 255)  # Белый

SIZES = [
    (16, 16, "favicon-16x16.png"),
    (32, 32, "favicon-32x32.png"),
    (48, 48, "favicon-48x48.png"),
    (192, 192, "android-chrome-192x192.png"),
    (512, 512, "android-chrome-512x512.png"),
    (180, 180, "apple-touch-icon.png"),
]


def create_pen_icon(size):
    """Создает иконку с пером"""
    img = Image.new('RGBA', (size, size), BG_COLOR + (255,))
    draw = ImageDraw.Draw(img)

    # Рассчитываем размеры пера
    center_x = size // 2
    center_y = size // 2
    pen_height = int(size * 0.7)
    pen_width = int(size * 0.15)

    # Координаты пера
    top_y = center_y - pen_height // 2
    bottom_y = center_y + pen_height // 2

    # Рисуем корпус пера (трапеция)
    pen_top_width = pen_width
    pen_bottom_width = int(pen_width * 1.3)

    pen_coords = [
        (center_x - pen_top_width // 2, top_y),
        (center_x + pen_top_width // 2, top_y),
        (center_x + pen_bottom_width // 2, bottom_y - int(size * 0.15)),
        (center_x - pen_bottom_width // 2, bottom_y - int(size * 0.15))
    ]
    draw.polygon(pen_coords, fill=PEN_COLOR)

    # Рисуем наконечник (треугольник)
    nib_coords = [
        (center_x - pen_bottom_width // 2, bottom_y - int(size * 0.15)),
        (center_x + pen_bottom_width // 2, bottom_y - int(size * 0.15)),
        (center_x, bottom_y)
    ]
    draw.polygon(nib_coords, fill=(74, 74, 74))

    # Добавляем острие
    tip_coords = [
        (center_x - 1, bottom_y - 3),
        (center_x + 1, bottom_y - 3),
        (center_x, bottom_y)
    ]
    draw.polygon(tip_coords, fill=(26, 26, 26))

    # Добавляем блик если размер достаточно большой
    if size >= 32:
        highlight_width = max(2, pen_width // 4)
        highlight_x = center_x + pen_width // 4
        highlight_top = top_y + int(pen_height * 0.2)
        highlight_bottom = top_y + int(pen_height * 0.6)
        draw.line(
            [(highlight_x, highlight_top), (highlight_x, highlight_bottom)],
            fill=(255, 255, 255, 100),
            width=highlight_width
        )

    return img


def create_ico(png_paths, ico_path):
    """Создает ICO файл из PNG"""
    images = []
    for png_path in png_paths:
        if png_path.exists():
            img = Image.open(png_path)
            images.append(img)

    if images:
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )
        print(f"✅ Создан: {ico_path.name}")


def main():
    print("=" * 60)
    print("Генерация фавиконов для Penița Dreptului")
    print("=" * 60)
    print()

    png_paths = []

    for width, height, filename in SIZES:
        output_path = STATIC_IMG / filename

        # Создаем изображение
        img = create_pen_icon(width)

        # Сохраняем
        img.save(output_path, 'PNG')
        print(f"✅ Создан: {filename} ({width}x{height})")

        if width <= 48:  # Только маленькие размеры для ICO
            png_paths.append(output_path)

    print()

    # Создаем ICO
    ico_path = STATIC_IMG / "favicon.ico"
    create_ico(png_paths, ico_path)

    print()
    print("=" * 60)
    print("✅ Все фавиконы созданы!")
    print("=" * 60)
    print()
    print("Следующий шаг: обновите templates/base.html")


if __name__ == "__main__":
    main()
