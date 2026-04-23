import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import AmenityCategory, Amenity, AmenityName

# Для кожної існуючої послуги створюємо запис у AmenityName
for amenity in Amenity.objects.all():
    name_obj, created = AmenityName.objects.get_or_create(
        category=amenity.category,
        name=amenity.name,
        defaults={
            'order': amenity.order,
            'is_popular_default': amenity.is_popular
        }
    )
    if created:
        print(f"Додано назву: {amenity.name} для категорії {amenity.category.name}")