import os
import django
import sys
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import Tour
from users.models import User

# Получаем первого агента (или создаем тестового)
try:
    agent = User.objects.filter(is_agent=True).first()
    if not agent:
        agent = User.objects.create_user(
            username='test_agent',
            password='testpass123',
            is_agent=True
        )
        print("Создан тестовый агент")
except:
    print("Ошибка при получении агента")
    sys.exit(1)

# Создаем тестовые туры с разными странами
tours_data = [
    {
        'title': 'Відпочинок в Єгипті',
        'country': 'Єгипет',
        'description': 'Чудовий відпочинок на березі Червоного моря. Все включено!',
        'price': 1200.00,
        'start_date': date.today() + timedelta(days=30),
        'end_date': date.today() + timedelta(days=44),
    },
    {
        'title': 'Тур в Карпати',
        'country': 'Україна',
        'description': 'Активний відпочинок в горах. Піші прогулянки та екскурсії.',
        'price': 450.00,
        'start_date': date.today() + timedelta(days=15),
        'end_date': date.today() + timedelta(days=22),
    },
    {
        'title': 'Екскурсія до Львова',
        'country': 'Україна',
        'description': 'Знайомство з культурою та архітектурою Львова.',
        'price': 250.00,
        'start_date': date.today() + timedelta(days=10),
        'end_date': date.today() + timedelta(days=14),
    },
]

for data in tours_data:
    tour, created = Tour.objects.get_or_create(
        title=data['title'],
        defaults={
            'country': data['country'],
            'description': data['description'],
            'price': data['price'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'author': agent,
            # image можно оставить пустым или добавить заглушку
        }
    )
    if created:
        print(f"Создан тур: {tour.title}")
    else:
        print(f"Тур уже существует: {tour.title}")

print("\nВсего туров в базе:", Tour.objects.count())