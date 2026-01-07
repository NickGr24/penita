#!/usr/bin/env python3
"""
Скрипт для генерации фавиконов разных размеров из SVG
Требует: pip install Pillow cairosvg
"""

import os
from pathlib import Path

try:
    from PIL import Image
    import cairosvg
except ImportError:
    print("❌ Требуется установка: pip install Pillow cairosvg")
    exit(1)

# Пути
BASE_DIR = Path(__file__).resolve().parent
STATIC_IMG = BASE_DIR / "main/static/img"
SVG_SOURCE = STATIC_IMG / "favicon.svg"
APPLE_SVG_SOURCE = STATIC_IMG / "apple-touch-icon.svg"

# Размеры для генерации
FAVICON_SIZES = [
    (16, 16, "favicon-16x16.png"),
    (32, 32, "favicon-32x32.png"),
    (48, 48, "favicon-48x48.png"),  # Минимальный размер для Google
    (192, 192, "android-chrome-192x192.png"),  # Android
    (512, 512, "android-chrome-512x512.png"),  # Android HD
]

APPLE_SIZES = [
    (180, 180, "apple-touch-icon.png"),  # iOS
]


def svg_to_png(svg_path, output_path, width, height):
    """Конвертирует SVG в PNG указанного размера"""
    try:
        # Конвертируем SVG в PNG
        png_data = cairosvg.svg2png(
            url=str(svg_path),
            output_width=width,
            output_height=height
        )

        # Сохраняем
        with open(output_path, 'wb') as f:
            f.write(png_data)

        print(f"✅ Создан: {output_path.name} ({width}x{height})")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании {output_path.name}: {e}")
        return False


def create_ico(png_paths, ico_path):
    """Создает ICO файл из PNG изображений"""
    try:
        # Читаем PNG изображения
        images = []
        for png_path in png_paths:
            if png_path.exists():
                img = Image.open(png_path)
                images.append(img)

        if not images:
            print("❌ Нет PNG изображений для создания ICO")
            return False

        # Сохраняем как ICO
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )

        print(f"✅ Создан: {ico_path.name} (мультиразмерный ICO)")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании ICO: {e}")
        return False


def main():
    print("=" * 60)
    print("Генерация фавиконов для Penița Dreptului")
    print("=" * 60)
    print()

    # Проверяем наличие SVG файлов
    if not SVG_SOURCE.exists():
        print(f"❌ Файл не найден: {SVG_SOURCE}")
        return

    if not APPLE_SVG_SOURCE.exists():
        print(f"⚠️  Файл не найден: {APPLE_SVG_SOURCE}, используем основной SVG")

    # Генерируем основные фавиконы
    print("Генерация фавиконов...")
    png_paths = []
    for width, height, filename in FAVICON_SIZES:
        output_path = STATIC_IMG / filename
        if svg_to_png(SVG_SOURCE, output_path, width, height):
            png_paths.append(output_path)

    print()

    # Генерируем Apple Touch Icon
    print("Генерация Apple Touch Icon...")
    apple_svg = APPLE_SVG_SOURCE if APPLE_SVG_SOURCE.exists() else SVG_SOURCE
    for width, height, filename in APPLE_SIZES:
        output_path = STATIC_IMG / filename
        svg_to_png(apple_svg, output_path, width, height)

    print()

    # Создаем ICO файл
    print("Генерация favicon.ico...")
    ico_path = STATIC_IMG / "favicon.ico"
    # Используем только маленькие размеры для ICO (16, 32, 48)
    ico_pngs = [p for p in png_paths if any(s in p.name for s in ['16x16', '32x32', '48x48'])]
    create_ico(ico_pngs, ico_path)

    print()
    print("=" * 60)
    print("✅ Генерация завершена!")
    print("=" * 60)
    print()
    print("Созданные файлы:")
    for size, _, filename in FAVICON_SIZES + APPLE_SIZES:
        print(f"  - {filename}")
    print(f"  - favicon.ico")
    print()
    print("Следующий шаг: обновите теги в templates/base.html")


if __name__ == "__main__":
    main()
