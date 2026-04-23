import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject1.settings')
django.setup()

from tours.models import AmenityCategory, AmenityName

# Спочатку створюємо категорії (якщо їх ще немає)
categories_data = [
    {'name': 'Найпопулярніші зручності', 'order': 1},
    {'name': 'Пляж', 'order': 2},
    {'name': 'Спорт і розваги', 'order': 3},
    {'name': 'В готелі', 'order': 4},
    {'name': 'Для дітей', 'order': 5},
    {'name': 'Реновація', 'order': 6},
    {'name': 'Номери', 'order': 7},
    {'name': 'Особливості готелю', 'order': 8},
]

cat_objs = {}
for cat_data in categories_data:
    obj, created = AmenityCategory.objects.get_or_create(
        name=cat_data['name'],
        defaults={'order': cat_data['order']}
    )
    cat_objs[cat_data['name']] = obj
    if created:
        print(f'Створено категорію: {cat_data["name"]}')

# Словник: категорія -> список послуг (з позначкою популярності)
amenities_data = {
    'Найпопулярніші зручності': [
        ('Аквапарк або гірки', True),
        ('Готель для дорослих', True),
        ('Безвітряна бухта', True),
        ('Перша лінія', True),
        ('Друга лінія', False),
        ('Третя лінія і далі', False),
        ('Кораловий риф', True),
        ('Піщаний пляж', True),
        ('Піщано-гальковий пляж', False),
        ('Велика територія', True),
    ],
    'Пляж': [
        ('Кораловий риф', True),
        ('Власний пляж', True),
        ('Піщаний пляж', True),
        ('Шезлонги', True),
        ('Пляжні рушники', True),
        ('Понтон або пірс', True),
        ('Парасольки', True),
        ('Перша лінія', True),
    ],
    'Спорт і розваги': [
        ('Спа або велнес-центр', True),
        ('Гольф', False),
        ('Сауна/лазня/хамам', True),
        ('Дайвінг', True),
        ('Тренажерний зал', True),
        ('Джакузі', True),
        ('Серфінг', True),
        ('Аеробіка', False),
        ('Аквапарк або гірки', True),
        ('Футбольне поле', False),
        ('Анімація', True),
        ('Більярд', True),
        ('Організація екскурсій', True),
        ('Волейбол', True),
        ('Віндсерфінг', True),
        ('Настільний теніс', True),
        ('Тенісний корт', True),
        ('Водні розваги', True),
    ],
    'Номери': [
        ('Кабельне/супутникове ТВ', True),
        ('Сейф', True),
        ('Телефон', True),
        ('Холодильник', True),
        ('Ванна/душ', True),
        ('Кухня/кухонний куток', True),
        ('Інтернет wi-fi', True),
        ('Балкон/тераса', True),
        ('Фен', True),
        ('Кондиціонер', True),
    ],
    'В готелі': [
        ('Банкомат', True),
        ('Кафе/бар', True),
        ('Сейф', True),
        ('Оплата платіжними картами', True),
        ('Перукарня/салон краси', True),
        ('Лікар', True),
        ('Пральня', True),
        ('Автостоянка', True),
        ('Прокат автомобілів', True),
        ('Трансфер в/з аеропорту', True),
        ('Ресторан a la carte', True),
        ('Конференц-зал/банкетний зал', True),
        ('Обмін валют', True),
        ('Велика територія', True),
        ('Ресторан', True),
        ('Басейн з підігрівом', True),
        ('Номери для некурящих', True),
        ('Відкритий басейн', True),
    ],
    'Особливості готелю': [
        ('Хіт продажу 2018', True),
        ('Хіт продажу 2019', True),
    ],
    'Для дітей': [
        ('Дитяче ліжко', True),
        ('Дитячий клуб', True),
        ('Дитяче меню в ресторані', True),
        ('Дитячий басейн', True),
        ('Дитячі стільчиками в ресторані', True),
        ('Дитячий майданчик', True),
    ],
    'Реновація': [
        ('Реновація у 2019', True),
    ],
}

# Створення записів у AmenityName
for cat_name, items in amenities_data.items():
    category = cat_objs[cat_name]
    for order, (amenity_name, is_popular) in enumerate(items):
        obj, created = AmenityName.objects.get_or_create(
            category=category,
            name=amenity_name,
            defaults={
                'order': order,
                'is_popular_default': is_popular
            }
        )
        if created:
            print(f'Додано назву: {amenity_name} у категорію {cat_name}')