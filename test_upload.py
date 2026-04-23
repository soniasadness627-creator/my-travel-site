import os
import django
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import Tour

print("=" * 50)
print("ПРОВЕРКА ЗАГРУЗКИ ФОТО")
print("=" * 50)

# Проверяем все туры
tours = Tour.objects.all()
print(f"\nНайдено туров: {tours.count()}")

for tour in tours:
    print(f"\n--- Тур: {tour.title} (ID: {tour.id}) ---")

    # Проверяем главное фото
    if tour.image:
        print(f"Главное фото URL: {tour.image.url}")
        print(f"Главное фото путь: {tour.image.path}")
        print(f"Файл существует: {os.path.exists(tour.image.path)}")

        # Показываем правильный URL для браузера
        print(f"URL для браузера: http://127.0.0.1:8000{tour.image.url}")
    else:
        print("Главное фото: НЕТ")

    # Проверяем галерею
    gallery = tour.gallery.all()
    print(f"Фото в галерее: {gallery.count()}")
    for i, img in enumerate(gallery, 1):
        print(f"\n  Галерея фото {i}:")
        print(f"    URL: {img.image.url}")
        print(f"    Путь: {img.image.path}")
        print(f"    Файл существует: {os.path.exists(img.image.path)}")
        print(f"    URL для браузера: http://127.0.0.1:8000{img.image.url}")

print("\n" + "=" * 50)
print("ПРОВЕРКА ПАПОК")
print("=" * 50)

# Проверяем папки
media_path = os.path.join(os.path.dirname(__file__), 'DjangoProject1', 'media')
print(f"Media путь: {media_path}")
print(f"Media папка существует: {os.path.exists(media_path)}")

if os.path.exists(media_path):
    print("\nСодержимое media папки:")
    for root, dirs, files in os.walk(media_path):
        level = root.replace(media_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

print("\n" + "=" * 50)
print("ПРОВЕРКА НАСТРОЕК DJANGO")
print("=" * 50)

from django.conf import settings

print(f"MEDIA_URL: {settings.MEDIA_URL}")
print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
print(f"BASE_DIR: {settings.BASE_DIR}")
print(f"DEBUG: {settings.DEBUG}")