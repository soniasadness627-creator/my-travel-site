import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import Tour, Amenity

# Отримуємо всі зручності категорії "Пляж"
beach_amenities = Amenity.objects.filter(category__name='Пляж')
print(f"Знайдено пляжних зручностей: {beach_amenities.count()}")

# Додаємо до кожного туру
tours = Tour.objects.all()
for tour in tours:
    tour.amenities.add(*beach_amenities)
    print(f"Додано пляжні зручності до {tour.title}")

# Також додаємо кілька спортивних зручностей для різноманіття
sport_amenities = Amenity.objects.filter(category__name='Спорт і розваги')[:5]
for tour in tours:
    tour.amenities.add(*sport_amenities)
    print(f"Додано спортивні зручності до {tour.title}")