import os
import django
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import Tour
from users.models import User

agent = User.objects.filter(is_agent=True).first()
if not agent:
    agent = User.objects.create_user('temp_agent', 'temp@example.com', 'temp123', is_agent=True)

base_tour = Tour.objects.first()
if not base_tour:
    print("Немає жодного туру. Спочатку додайте хоча б один тур через адмінку.")
    exit()

for delta in [-10, -5, 5, 10]:
    # Конвертуємо множник у Decimal
    multiplier = Decimal(1 + delta / 100)
    new_price = base_tour.price * multiplier
    tour, created = Tour.objects.get_or_create(
        title=f"{base_tour.title} (ціна {new_price:.0f})",
        defaults={
            'country': base_tour.country,
            'price': new_price.quantize(Decimal('0.01')),  # округлюємо до 2 знаків
            'start_date': base_tour.start_date + timedelta(days=7),
            'end_date': base_tour.end_date + timedelta(days=7),
            'author': agent,
            'description': base_tour.description,
        }
    )
    if created:
        print(f"Створено тур: {tour.title} з ціною {tour.price}")
    else:
        print(f"Тур {tour.title} вже існує")