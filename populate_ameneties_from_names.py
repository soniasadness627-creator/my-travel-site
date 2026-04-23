import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import AmenityName, Amenity

for name_obj in AmenityName.objects.all():
    amenity, created = Amenity.objects.get_or_create(
        category=name_obj.category,
        name=name_obj,
        defaults={
            'order': name_obj.order,
            'is_popular': name_obj.is_popular_default
        }
    )
    if created:
        print(f'Створено послугу: {amenity}')

print("Готово!")
