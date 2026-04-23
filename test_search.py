import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import Tour
from django.db.models import Q

print("=" * 50)
print("ПРОВЕРКА ПОИСКА")
print("=" * 50)

# Показываем все туры в базе
tours = Tour.objects.all()
print(f"\nВсего туров в базе: {tours.count()}")
for tour in tours:
    print(f"  - {tour.title} (Страна: {tour.country})")

# Тестируем поиск
test_queries = ['тур', 'італія', 'відпочинок', '']  # Добавьте свои тестовые запросы

for query in test_queries:
    if not query:
        continue

    print(f"\n--- Поиск: '{query}' ---")

    words = query.lower().split()
    search_query = Q()

    for word in words:
        if len(word) < 2:
            continue
        search_query |= Q(title__icontains=word)
        search_query |= Q(description__icontains=word)
        search_query |= Q(country__icontains=word)

    results = Tour.objects.filter(search_query).distinct()
    print(f"Найдено: {results.count()}")
    for tour in results:
        print(f"  - {tour.title} (Страна: {tour.country})")