import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import Tour
from django.conf import settings

print("ПРОВЕРКА URL ФОТОГРАФИЙ")
print("=" * 60)

for tour in Tour.objects.all():
    print(f"\nТур: {tour.title}")

    if tour.image:
        print(f"  Главное фото: {tour.image.url}")
        print(f"  Полный URL: http://127.0.0.1:8000{tour.image.url}")
        print(f"  Путь на диске: {tour.image.path}")
        print(f"  Файл существует: {os.path.exists(tour.image.path)}")

    for i, img in enumerate(tour.gallery.all(), 1):
        print(f"  Галерея {i}: {img.image.url}")
        print(f"    Полный URL: http://127.0.0.1:8000{img.image.url}")
        print(f"    Путь на диске: {img.image.path}")
        print(f"    Файл существует: {os.path.exists(img.image.path)}")