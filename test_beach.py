# test_beach.py
# Запуск: python manage.py shell < test_beach.py

from tours.models import Tour
from django.db import models

# Вкажіть ID туру, для якого хочете перевірити (замініть 1 на потрібний ID)
tour_id = 1

try:
    tour = Tour.objects.get(pk=tour_id)
except Tour.DoesNotExist:
    print(f"Тур з ID {tour_id} не знайдено!")
    exit()

print("=" * 50)
print(f"ПОТОЧНИЙ ТУР: {tour.title} (ID: {tour.id})")
print(f"Країна: {tour.country}")
print(f"Ціна: {tour.price}")
print("=" * 50)

# ---- 1. Перевіряємо зручності пляжу поточного туру ----
print("\n1. ЗРУЧНОСТІ КАТЕГОРІЇ 'ПЛЯЖ' У ПОТОЧНОМУ ТУРІ:")
beach_amenities = tour.amenities.filter(category__name__icontains='пляж')

if not beach_amenities.exists():
    print("   ✗ Не знайдено жодної зручності, що містить 'пляж' у назві категорії.")
    print("   Спробуйте інший фільтр, наприклад:")
    print("   - category__name='Пляж' (точна назва)")
    print("   - name__icontains='пляж' (пошук у назві зручності)")
else:
    print(f"   ✓ Знайдено {beach_amenities.count()} зручностей:")
    for a in beach_amenities:
        print(f"      - {a.name} (категорія: {a.category.name})")

beach_amenity_ids = list(beach_amenities.values_list('id', flat=True))

# ---- 2. Шукаємо інші тури з такими ж зручностями ----
print("\n2. ПОШУК ІНШИХ ТУРІВ З АНАЛОГІЧНИМИ ЗРУЧНОСТЯМИ:")

if beach_amenity_ids:
    similar_tours = Tour.objects.exclude(pk=tour.pk).filter(
        amenities__id__in=beach_amenity_ids
    ).distinct().annotate(
        reviews_count=models.Count('reviews')
    )[:10]

    if similar_tours.exists():
        print(f"   ✓ Знайдено {similar_tours.count()} турів:")
        for t in similar_tours:
            common = t.amenities.filter(id__in=beach_amenity_ids)
            print(f"      - {t.title} (ID: {t.id})")
            print(f"        Спільні зручності: {', '.join([a.name for a in common])}")
    else:
        print("   ✗ Немає інших турів із такими зручностями.")
        print("   Можливо, в базі недостатньо даних або потрібно розширити пошук.")
else:
    print("   ✗ Пропускаємо пошук, оскільки немає зручностей для порівняння.")

# ---- 3. Альтернативний пошук за назвою зручності (без категорії) ----
print("\n3. АЛЬТЕРНАТИВНИЙ ПОШУК (за назвою зручності, що містить 'пляж'):")
beach_by_name = tour.amenities.filter(name__icontains='пляж')
if beach_by_name.exists():
    print(f"   Знайдено {beach_by_name.count()} зручностей за назвою:")
    for a in beach_by_name:
        print(f"      - {a.name}")

    name_ids = list(beach_by_name.values_list('id', flat=True))
    similar_by_name = Tour.objects.exclude(pk=tour.pk).filter(
        amenities__id__in=name_ids
    ).distinct()[:10]

    if similar_by_name.exists():
        print(f"   ✓ Знайдено {similar_by_name.count()} турів за назвою:")
        for t in similar_by_name:
            print(f"      - {t.title}")
    else:
        print("   ✗ Немає інших турів із такими зручностями за назвою.")
else:
    print("   ✗ Не знайдено зручностей зі словом 'пляж' у назві.")

# ---- 4. Перевірка, чи передається змінна в контекст (опціонально) ----
print("\n4. ПЕРЕВІРКА КОНТЕКСТУ (для розробника):")
print("   У функції tour_detail має бути:")
print("   'beach_similar_tours': beach_similar_tours,")
print("   Якщо блок не відображається, переконайтеся, що змінна передається.")
print("=" * 50)