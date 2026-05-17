import requests
import json
import random
import re
from django.core.cache import cache
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Tour, News, Review, Consultation, Booking, HotelReview, PriceCalendar, PopularHotel
from .forms import ConsultationForm, ReviewForm

User = get_user_model()


# ========== ДОПОМІЖНА ФУНКЦІЯ ДЛЯ ОТРИМАННЯ ВИПАДКОВОГО АГЕНТА ==========
def get_random_agent():
    """Повертає випадкового агента для блоку консультації"""
    agents = User.objects.filter(is_agent=True)
    if agents.exists():
        return random.choice(agents)
    return None


# ========== ВИПРАВЛЕНА ФУНКЦІЯ ДЛЯ РОЗРАХУНКУ ДНІВ У МІСЯЦІ ==========
def get_days_in_month(year, month):
    """Безпечно повертає кількість днів у місяці"""
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    return last_day.day


def get_realistic_prices(month, year, country, departure):
    """
    Генерує реалістичні ціни на основі країни та міста вильоту
    """
    # БЕЗПЕЧНЕ ВИЗНАЧЕННЯ КІЛЬКОСТІ ДНІВ У МІСЯЦІ
    days_in_month = get_days_in_month(year, month)

    # ========== БАЗОВІ ЦІНИ ДЛЯ КРАЇН ==========
    country_prices = {
        'Єгипет': (40000, 55500),
        'Туреччина': (37000, 58000),
        'ОАЕ': (37000, 55000),
        'Шрі-Ланка': (81000, 161000),
        'Іспанія': (41000, 70000),
        'Мальдіви': (148000, 207000),
        'Кіпр': (33000, 35000),
        'Чорногорія': (73000, 98000),
        'Хорватія': (81000, 98000),
        'Греція': (22000, 38000),
        'Туніс': (59000, 62000),
        'Таїланд': (130000, 132000),
        'Грузія': (28000, 29900),
        'Чехія': (56000, 58000),
        'Індонезія': (138000, 303419),
        'Маврикій': (150000, 426000),
        'Португалія': (197000, 197930),
        'Італія': (45000, 85000),
    }

    # ========== КОЕФІЦІЄНТИ ДЛЯ РІЗНИХ МІСТ ВИЛЬОТУ ==========
    departure_factors = {
        'Кишинів': 1.00,
        'Кишинев': 1.00,
        'Варшава': 1.15,
        'Краків': 1.12,
        'Бухарест': 1.05,
        'Будапешт': 1.10,
        'Берлін': 1.25,
        'Прага': 1.18,
        'Тбілісі': 1.08,
        'Стамбул': 1.12,
        'Київ': 0.95,
        'Одеса': 0.98,
        'Львів': 0.97,
        'Харків': 0.96,
    }

    # Отримуємо діапазон цін для країни
    if country and country in country_prices:
        min_price, max_price = country_prices[country]
    else:
        min_price, max_price = 30000, 70000

    # Отримуємо коефіцієнт для міста вильоту
    factor = departure_factors.get(departure, 1.00)

    # Застосовуємо коефіцієнт до діапазону
    min_price = int(min_price * factor)
    max_price = int(max_price * factor)

    # Сезонні коефіцієнти
    seasonal_factor = 1.0
    if month in [6, 7, 8]:  # літо
        seasonal_factor = 1.15
    elif month in [1, 2, 12]:  # зима
        seasonal_factor = 0.9

    # Використовуємо стабільний seed для однакових даних
    seed_value = year * 12 + month
    random.seed(seed_value)

    prices = []
    for day in range(1, days_in_month + 1):
        # Генеруємо ціну в заданому діапазоні
        price_range = max_price - min_price
        price = min_price + (price_range * random.random())

        # Додаємо сезонний коефіцієнт
        price = price * seasonal_factor

        # Вихідні дорожчі на 10-20%
        is_weekend = (day % 7 in [0, 1, 6])
        if is_weekend:
            price = price * random.uniform(1.1, 1.2)

        # Додаємо випадкову варіацію для різних днів
        day_variation = random.uniform(0.95, 1.05)
        price = price * day_variation

        # Округлюємо до 50 гривень
        price = int(round(price / 50) * 50)

        # Обмежуємо діапазон
        price = max(20000, min(250000, price))

        prices.append(price)

    max_price = max(prices)

    return {'prices': prices, 'max_price': max_price}


# ========== API ДЛЯ КАЛЕНДАРЯ НИЗЬКИХ ЦІН ==========
def calendar_prices_otpusk(request):
    """
    API для календаря низьких цін (демо-дані з реалістичними цінами)
    """
    country = request.GET.get('country')
    year = request.GET.get('year')
    month = request.GET.get('month')
    departure = request.GET.get('departure')
    slug = request.GET.get('slug')

    if not all([country, year, month]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        return JsonResponse({'error': 'Invalid year/month'}, status=400)

    result = get_realistic_prices(month, year, country, departure)
    return JsonResponse(result)


# ========== API З КЕШУВАННЯМ ДЛЯ КАЛЕНДАРЯ (ГОЛОВНИЙ) ==========
def calendar_prices_cached(request):
    """
    API для календаря низьких цін з кешуванням
    """
    country = request.GET.get('country')
    year = request.GET.get('year')
    month = request.GET.get('month')
    departure = request.GET.get('departure')
    slug = request.GET.get('slug')

    if not all([country, year, month]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        return JsonResponse({'error': 'Invalid year/month'}, status=400)

    # Формуємо ключ для кешу
    cache_key = f"calendar_prices_{country}_{year}_{month}_{departure}_{slug}"

    # Перевіряємо, чи є дані в кеші
    cached_data = cache.get(cache_key)
    if cached_data:
        print(f"✅ Дані з кешу для {country} ({year}-{month})")
        return JsonResponse(cached_data)

    # Якщо немає в кеші – отримуємо ціни
    print(f"🔄 Отримуємо ціни для {country} ({year}-{month})")

    try:
        result = get_realistic_prices(month, year, country, departure)
        # Зберігаємо в кеш на 24 години
        cache.set(cache_key, result, 86400)
        print(f"💾 Збережено в кеш для {country} ({year}-{month})")
        return JsonResponse(result)
    except Exception as e:
        print(f"❌ Помилка генерації цін: {e}")
        # Повертаємо пусті дані, але без помилки 500
        days_in_month = get_days_in_month(year, month)
        empty_prices = [None] * days_in_month
        return JsonResponse({'prices': empty_prices, 'max_price': None})


# ========== API ДЛЯ РЕАЛЬНИХ ЦІН З OTPUSK ==========
def calendar_prices_from_otpusk(request):
    """
    API для отримання реальних цін безпосередньо з Otpusk.com
    """
    country = request.GET.get('country')
    year = request.GET.get('year')
    month = request.GET.get('month')
    departure = request.GET.get('departure')
    slug = request.GET.get('slug')

    if not all([country, year, month]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        return JsonResponse({'error': 'Invalid year/month'}, status=400)

    # ПОВНА МАПА КРАЇН ДЛЯ OTPUSK API
    country_map = {
        'Єгипет': 'Egypt',
        'Туреччина': 'Turkey',
        'ОАЕ': 'UAE',
        'Шрі-Ланка': 'Sri Lanka',
        'Іспанія': 'Spain',
        'Мальдіви': 'Maldives',
        'Кіпр': 'Cyprus',
        'Чорногорія': 'Montenegro',
        'Хорватія': 'Croatia',
        'Греція': 'Greece',
        'Туніс': 'Tunisia',
        'Таїланд': 'Thailand',
        'Грузія': 'Georgia',
        'Італія': 'Italy',
        'Португалія': 'Portugal',
    }

    # ПОВНА МАПА МІСТ ВИЛЬОТУ
    departure_map = {
        'Кишинів': 'Chisinau',
        'Кишинев': 'Chisinau',
        'Варшава': 'Warsaw',
        'Краків': 'Krakow',
        'Бухарест': 'Bucharest',
        'Будапешт': 'Budapest',
        'Берлін': 'Berlin',
        'Прага': 'Prague',
        'Тбілісі': 'Tbilisi',
        'Стамбул': 'Istanbul',
        'Київ': 'Kyiv',
        'Одеса': 'Odessa',
        'Львів': 'Lviv',
        'Харків': 'Kharkiv',
    }

    # Конвертуємо назви
    api_country = country_map.get(country, country)
    api_departure = departure_map.get(departure, departure or 'Chisinau')

    # Визначаємо діапазон дат
    if month == 12:
        start_date = f"{year}-12-01"
        end_date = f"{year + 1}-01-01"
        days_in_month = 31
    else:
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month + 1:02d}-01"
        from datetime import date
        days_in_month = (date(year, month + 1, 1) - date(year, month, 1)).days

    otpusk_url = "https://export.otpusk.com/api/2.4/search"
    params = {
        'country': api_country,
        'departure': api_departure,
        'date_from': start_date,
        'date_to': end_date,
        'format': 'json',
        'access_token': '3f94b-e4ff8-a72a7-4755f-da9ca'
    }

    if slug:
        params['slug'] = slug

    try:
        response = requests.get(otpusk_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            prices_by_day = {}

            if 'tours' in data:
                for tour in data['tours']:
                    start_date_str = tour.get('start_date')
                    price = tour.get('price')
                    if start_date_str and price:
                        try:
                            day = int(start_date_str.split('-')[2])
                            price_int = int(price)
                            if day not in prices_by_day or price_int < prices_by_day[day]:
                                prices_by_day[day] = price_int
                        except:
                            pass

            prices = []
            for day in range(1, days_in_month + 1):
                prices.append(prices_by_day.get(day, None))

            if any(prices):
                max_price = max([p for p in prices if p], default=50000)
                return JsonResponse({'prices': prices, 'max_price': max_price})
            else:
                return JsonResponse(get_realistic_prices(month, year, country, departure))
        else:
            return JsonResponse(get_realistic_prices(month, year, country, departure))
    except Exception as e:
        print(f"Помилка Otpusk API: {e}")
        return JsonResponse(get_realistic_prices(month, year, country, departure))


# ========== API ДЛЯ КАЛЕНДАРЯ НИЗЬКИХ ЦІН (З БАЗИ ДАНИХ) ==========
def calendar_prices_from_db(request):
    """API для отримання реальних цін з бази даних"""
    country = request.GET.get('country')
    year = request.GET.get('year')
    month = request.GET.get('month')
    departure = request.GET.get('departure')

    if not all([country, year, month]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        return JsonResponse({'error': 'Invalid year/month'}, status=400)

    from datetime import date
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    tours = Tour.objects.filter(
        country__icontains=country,
        departure_city__icontains=departure
    )

    prices_by_day = {}
    for tour in tours:
        price_options = PriceCalendar.objects.filter(
            tour=tour,
            date__gte=start_date,
            date__lt=end_date
        ).values('date').annotate(min_price=models.Min('price'))

        for option in price_options:
            day = option['date'].day
            price = option['min_price']
            if price and (day not in prices_by_day or price < prices_by_day[day]):
                prices_by_day[day] = int(price) if price else 0

    days_in_month = (end_date - start_date).days
    prices = []
    for day in range(1, days_in_month + 1):
        prices.append(prices_by_day.get(day, None))

    max_price = max([p for p in prices if p is not None], default=50000)
    return JsonResponse({'prices': prices, 'max_price': max_price})


# ========== API ДЛЯ ПОПУЛЯРНИХ ТУРІВ ==========
from datetime import datetime, timedelta


def get_popular_tours_api(request, slug=None):
    """
    API для отримання популярних турів з індивідуальними містами вильоту та фото
    """
    from .models import City
    from datetime import timedelta

    # Список країн з індивідуальними містами вильоту
    countries_config = [
        {'country': 'Єгипет', 'departure': 'Брно', 'departure_text': 'з Брно'},
        {'country': 'Туреччина', 'departure': 'Берлін', 'departure_text': 'з Берліна'},
        {'country': 'ОАЕ', 'departure': 'Варшава', 'departure_text': 'з Варшави'},
        {'country': 'Греція', 'departure': 'Відень', 'departure_text': 'з Відня'},
        {'country': 'Кіпр', 'departure': 'Кишинів', 'departure_text': 'з Кишинева'},
        {'country': 'Іспанія', 'departure': 'Кишинів', 'departure_text': 'з Кишинева'},
        {'country': 'Таїланд', 'departure': 'Київ', 'departure_text': 'з Києва'},
        {'country': 'Мальдіви', 'departure': 'Кишинів', 'departure_text': 'з Кишинева'},
        {'country': 'Італія', 'departure': 'Краків', 'departure_text': 'з Кракова'},
        {'country': 'Хорватія', 'departure': 'Познань', 'departure_text': 'з Познані'},
        {'country': 'Чорногорія', 'departure': 'Вроцлав', 'departure_text': 'з Вроцлава'},
        {'country': 'Болгарія', 'departure': 'Київ', 'departure_text': 'з Києва'},
        {'country': 'Грузія', 'departure': 'Тбілісі', 'departure_text': 'з Тбілісі'},
        {'country': 'Польща', 'departure': 'Варшава', 'departure_text': 'з Варшави'},
        {'country': 'Угорщина', 'departure': 'Будапешт', 'departure_text': 'з Будапешта'},
        {'country': 'Чехія', 'departure': 'Прага', 'departure_text': 'з Праги'},
        {'country': 'Австрія', 'departure': 'Відень', 'departure_text': 'з Відня'},
        {'country': 'Франція', 'departure': 'Париж', 'departure_text': 'з Парижа'},
        {'country': 'Німеччина', 'departure': 'Берлін', 'departure_text': 'з Берліна'},
    ]

    # ФОТО ДЛЯ КОЖНОЇ КРАЇНИ (ВАШІ ЛОКАЛЬНІ ФОТО)
    country_images = {
        'Єгипет': '/static/images/Egypt.jpg',
        'Туреччина': '/static/images/Turkey.jpg',
        'ОАЕ': '/static/images/UAE.jpg',
        'Греція': '/static/images/Greece.jpg',
        'Кіпр': '/static/images/Cyprus.jpg',
        'Іспанія': '/static/images/Spain.jpg',
        'Таїланд': '/static/images/Thailand.jpg',
        'Мальдіви': '/static/images/maldives.jpg',
        'Італія': '/static/images/Italy.jpg',
        'Хорватія': '/static/images/Croatia.jpg',
        'Чорногорія': '/static/images/Montenegro.jpg',
        'Болгарія': '/static/images/Bulgaria.jpg',
        'Грузія': '/static/images/Georgia.jpg',
        'Польща': '/static/images/Poland.jpg',
        'Угорщина': '/static/images/Hungary.jpg',
        'Чехія': '/static/images/the Czech Republic.jpg',
        'Австрія': '/static/images/Austria.jpg',
        'Франція': '/static/images/France.jpg',
        'Німеччина': '/static/images/Germany.jpg',
        'Албанія': '/static/images/Albania.jpg',
        'Шрі Ланка': '/static/images/SriLanka.jpg',
        'В\'єтнам': '/static/images/Vietnam.jpg',
        'Туніс': '/static/images/Tunisia.jpg',
        'Домінікана': '/static/images/dominican.jpg',
        'Індонезія': '/static/images/Indonesia.jpg',
        'Маврикій': '/static/images/mauritius.jpg',
    }

    # Фото за замовчуванням (якщо якоїсь країни немає в списку)
    default_image = '/static/images/default-tour.jpg'

    tours = []
    current_month = datetime.now()

    for idx, config in enumerate(countries_config):
        country = config['country']
        departure_city = config['departure']
        departure_text = config['departure_text']

        # Отримуємо ціну
        price_data = get_realistic_prices(current_month.month, current_month.year, country, departure_city)

        if price_data and price_data.get('prices'):
            valid_prices = [p for p in price_data['prices'] if p is not None]
            price = min(valid_prices) if valid_prices else 50000
        else:
            price = 50000

        # Отримуємо перше місто для цієї країни
        first_city = City.objects.filter(country=country).first()
        city_name = first_city.name if first_city else 'популярний курорт'

        # Отримуємо фото (якщо немає в словнику, використовуємо фото за замовчуванням)
        image_url = country_images.get(country, default_image)

        # Генеруємо дати
        start_date = (datetime.now() + timedelta(days=14 + idx)).strftime('%Y-%m-%d')
        nights = str(7 + (idx % 4))
        hid = str(8000 + idx)
        oid = str(1000000000000000000 + idx)

        tours.append({
            'id': hid,
            'hid': hid,
            'oid': oid,
            'od': start_date,
            'ol': nights,
            'hotel': f"Подорож до {country}",
            'country': country,
            'city': city_name,
            'price': price,
            'stars': 5,
            'image': image_url,
            'departure': departure_city,
            'departure_text': departure_text
        })

    return JsonResponse({'tours': tours})


def add_fallback_tour(tours, country, idx):
    """Додає тур-заглушку якщо API не повернув дані"""
    from datetime import timedelta
    tours.append({
        'id': str(8000 + idx),
        'hid': str(8000 + idx),
        'oid': str(1000000000000000000 + idx),
        'od': (datetime.now() + timedelta(days=14 + idx)).strftime('%Y-%m-%d'),
        'ol': str(7 + (idx % 4)),
        'hotel': f"Подорож до {country}",
        'country': country,
        'city': 'популярний курорт',
        'price': 50000,
        'stars': 4,
        'image': f"https://images.pexels.com/photos/1268855/pexels-photo-1268855.jpeg?w=400&h=250&fit=crop",
        'departure': 'Кишинів'
    })


# ========== НОВИЙ API ДЛЯ ПОПУЛЯРНИХ ГОТЕЛІВ ==========
def get_popular_hotels_api(request, slug=None):
    """
    API для отримання випадкових 10 популярних готелів з бази даних
    (якщо в адмінці додано 30 - показує 10 випадкових)
    """
    # Отримуємо всі активні готелі
    all_hotels = list(PopularHotel.objects.filter(is_active=True))

    print(f"📊 Всього активних готелів в БД: {len(all_hotels)}")

    # Якщо готелів більше ніж 10, вибираємо випадкові 10
    if len(all_hotels) > 10:
        selected_hotels = random.sample(all_hotels, 10)
        print(f"🎲 Вибрано {len(selected_hotels)} випадкових готелів із {len(all_hotels)}")
    else:
        selected_hotels = all_hotels
        print(f"📋 Показано всі {len(selected_hotels)} готелі (менше або дорівнює 10)")

    # Перемішуємо для додаткового рандому порядку
    random.shuffle(selected_hotels)

    data = []
    for hotel in selected_hotels:
        # Отримуємо фото
        if hotel.image:
            image_url = hotel.image.url
        elif hotel.image_url:
            image_url = hotel.image_url
        else:
            image_url = '/static/images/default-hotel.jpg'

        data.append({
            'id': hotel.id,
            'hid': hotel.hid,
            'oid': hotel.oid,
            'od': hotel.od,
            'ol': hotel.ol,
            'hotel_name': hotel.hotel_name,
            'country': hotel.country,
            'city': hotel.city,
            'rating': float(hotel.rating) if hotel.rating else 8.0,
            'reviews_count': hotel.reviews_count,
            'price': float(hotel.price),
            'image': image_url,
        })

    return JsonResponse({'hotels': data})

def home(request):
    """Головна сторінка з пошуком Otpusk та календарем низьких цін"""
    agent_site = getattr(request, 'current_agent_site', None)

    context = {
        'agent_site': agent_site,
        'random_agent': get_random_agent(),  # ← ДОДАТИ ЦЕЙ РЯДОК
        'blocks_order': getattr(request, 'blocks_order', []),
        'active_blocks': getattr(request, 'active_blocks', []),
        'banners': getattr(request, 'banners', []),
        'custom_css': getattr(request, 'custom_css', ''),
        'custom_js': getattr(request, 'custom_js', ''),
    }
    return render(request, 'tours/home.html', context)


# ========== ОСНОВНІ ФУНКЦІЇ ДЛЯ АГЕНТСЬКИХ САЙТІВ ==========

def tour_detail(request, pk):
    """Деталі туру - використовує дані з Otpusk"""
    try:
        tour = get_object_or_404(Tour, pk=pk)
    except Http404:
        return redirect('/search-otpusk/')

    reviews = tour.reviews.all()
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
    gallery_images = tour.gallery.all()

    similar_tours = Tour.objects.filter(
        country=tour.country,
        stars=tour.stars
    ).exclude(pk=tour.pk)[:8]

    context = {
        'tour': tour,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'gallery_images': gallery_images,
        'similar_tours': similar_tours,
        'review_form': ReviewForm(),
    }
    return render(request, 'tours/tour_detail.html', context)


def search_results(request):
    """Результати пошуку - перенаправляємо на Otpusk"""
    query_params = request.GET.urlencode()
    if query_params:
        return redirect(f'/search-otpusk/?{query_params}')
    return redirect('/search-otpusk/')


def city_detail(request, city_id):
    """Деталі міста - перенаправляємо на пошук Otpusk"""
    from .models import City
    try:
        city = get_object_or_404(City, pk=city_id)
        return redirect(f'/search-otpusk/?country={city.country}')
    except:
        return redirect('/search-otpusk/')


def news_detail(request, pk):
    """Деталі новини"""
    news_item = get_object_or_404(News, pk=pk)
    recommended = News.objects.exclude(pk=pk).order_by('-created_at')[:4]

    context = {
        'news_item': news_item,
        'recommended': recommended,
    }
    return render(request, 'tours/news_detail.html', context)


def get_agent_colors(request):
    """Отримання кольорів агента"""
    if hasattr(request, 'agent_colors'):
        return request.agent_colors
    return {
        'primary_color': '#086745',
        'primary_dark': '#02432c',
        'primary_light': '#2a6b5c',
        'primary_lighter': '#cbf6ec',
    }


def tour_reviews(request, pk):
    """Всі відгуки про тур"""
    tour = get_object_or_404(Tour, pk=pk)
    reviews_list = tour.reviews.all()
    paginator = Paginator(reviews_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tours/tour_reviews.html', {
        'tour': tour,
        'page_obj': page_obj,
    })


def search_otpusk(request, slug=None):
    """
    Сторінка результатів пошуку турів через Otpusk API
    """
    # Отримуємо параметри з URL
    geo = request.GET.get('geo', '')
    departure_text = request.GET.get('departure_text', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    duration = request.GET.get('duration', '')
    auto_search = request.GET.get('auto_search', '1')

    agent_site = getattr(request, 'current_agent_site', None)

    context = {
        'agent_site': agent_site,
        'geo': geo,
        'departure_text': departure_text,
        'date_from': date_from,
        'date_to': date_to,
        'duration': duration,
        'auto_search': auto_search,
    }

    # ВАЖЛИВО: використовуємо правильний шаблон!
    return render(request, 'search_otpusk_results.html', context)

def search_results_calendar(request, slug=None):
    """Сторінка результатів пошуку для календаря низьких цін"""
    agent_site = getattr(request, 'current_agent_site', None)
    context = {'agent_site': agent_site}
    return render(request, 'tours/search_results_calendar.html', context)


def search_otpusk_by_country(request, slug=None):
    """Сторінка результатів пошуку для популярних напрямків (З БЛОКОМ КОНСУЛЬТАЦІЇ)"""
    agent_site = getattr(request, 'current_agent_site', None)
    country = request.GET.get('country', '')

    context = {
        'agent_site': agent_site,
        'selected_country': country,
        'random_agent': get_random_agent(),
    }
    return render(request, 'tours/search_results_by_country.html', context)


# ========== API ДЛЯ ВІДГУКІВ ==========
@csrf_exempt
@require_http_methods(["GET", "POST"])
def hotel_reviews_api(request, slug=None):
    """API для відгуків про готелі"""
    if request.method == 'GET':
        hid = request.GET.get('hid')
        if not hid:
            return JsonResponse({'error': 'hid required'}, status=400)

        reviews = HotelReview.objects.filter(hid=hid, is_approved=True).order_by('-created_at')
        data = {
            'reviews': [
                {
                    'id': r.id,
                    'guest_name': r.guest_name,
                    'rating': r.rating,
                    'comment': r.comment,
                    'created_at': r.created_at.isoformat()
                }
                for r in reviews
            ]
        }
        return JsonResponse(data)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            hid = data.get('hid')
            oid = data.get('oid')
            guest_name = data.get('guest_name', '').strip()
            rating = data.get('rating')
            comment = data.get('comment', '').strip()

            if not hid or not guest_name or not rating or not comment:
                return JsonResponse({'error': 'Всі поля обов\'язкові', 'success': False}, status=400)

            if rating < 1 or rating > 5:
                return JsonResponse({'error': 'Оцінка має бути від 1 до 5', 'success': False}, status=400)

            agent = None
            if slug:
                try:
                    from constructor.models.agent_site import AgentSite
                    agent_site = AgentSite.objects.filter(slug=slug).first()
                    if agent_site:
                        agent = agent_site.user
                except:
                    pass

            existing_review = HotelReview.objects.filter(hid=hid, guest_name=guest_name).first()

            if existing_review:
                existing_review.rating = rating
                existing_review.comment = comment
                existing_review.created_at = timezone.now()
                if agent and not existing_review.agent:
                    existing_review.agent = agent
                existing_review.save()
                return JsonResponse({'success': True, 'message': 'Ваш відгук оновлено!'})
            else:
                HotelReview.objects.create(
                    hid=hid, oid=oid, guest_name=guest_name,
                    rating=rating, comment=comment, agent=agent
                )
                return JsonResponse({'success': True, 'message': 'Дякуємо за ваш відгук!'})

        except Exception as e:
            print(f"Помилка: {e}")
            return JsonResponse({'error': str(e), 'success': False}, status=500)


def tour_detail_otpusk(request, slug=None):
    """Сторінка детального перегляду туру"""
    agent_site = getattr(request, 'current_agent_site', None)
    hid = request.GET.get('hid', '')
    oid = request.GET.get('oid', '')

    reviews = HotelReview.objects.filter(hid=hid, is_approved=True).order_by('-created_at')

    context = {
        'agent_site': agent_site,
        'random_agent': get_random_agent(),
        'hid': hid,
        'oid': oid,
        'od': request.GET.get('od', ''),
        'ol': request.GET.get('ol', ''),
        'reviews': reviews,
    }
    return render(request, 'tours/tour_detail_otpusk.html', context)


# ========== AJAX ОБРОБКА ==========
@csrf_exempt
@require_http_methods(["POST"])
def booking_ajax(request, slug=None):
    try:
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        tour_name = request.POST.get('tour_name', '').strip()
        tour_price = request.POST.get('tour_price', '').strip()
        tour_dates = request.POST.get('tour_dates', '').strip()
        country_code = request.POST.get('country_code', '+380')

        if not name or not phone or not email:
            return JsonResponse({'success': False, 'error': "Заповніть всі поля"})

        phone_clean = re.sub(r'[^0-9]', '', phone)
        full_phone = f"{country_code}{phone_clean}"

        full_message = f"Тур: {tour_name}\n"
        if tour_price:
            full_message += f"Ціна: {tour_price}\n"
        if tour_dates:
            full_message += f"Дати: {tour_dates}\n"
        if message:
            full_message += f"Коментар клієнта: {message}"

        booking = Booking.objects.create(
            tour=None, name=name, phone=full_phone,
            email=email, message=full_message
        )
        return JsonResponse({'success': True, 'message': 'Дякуємо! Наш менеджер зв\'яжеться з вами найближчим часом.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def consultation_ajax(request, slug=None):
    try:
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        comment = request.POST.get('comment', '').strip()
        country_code = request.POST.get('country_code', '+380')

        if not name:
            return JsonResponse({'success': False, 'error': "Введіть ваше ім'я"})
        if not phone:
            return JsonResponse({'success': False, 'error': "Введіть номер телефону"})

        phone_clean = re.sub(r'[^0-9]', '', phone)
        if len(phone_clean) < 9:
            return JsonResponse({'success': False, 'error': "Введіть коректний номер телефону (мінімум 9 цифр)"})

        full_phone = f"{country_code}{phone_clean}"

        consultation = Consultation.objects.create(name=name, phone=full_phone, comment=comment)

        if hasattr(request, 'current_agent_site') and request.current_agent_site:
            consultation.agent = request.current_agent_site.user
            consultation.save()
        elif slug:
            try:
                from constructor.models.agent_site import AgentSite
                agent_site = AgentSite.objects.filter(slug=slug).first()
                if agent_site:
                    consultation.agent = agent_site.user
                    consultation.save()
            except:
                pass

        return JsonResponse({'success': True, 'message': 'Дякуємо! Наш менеджер зв\'яжеться з вами найближчим часом.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== КЛАСИ ДЛЯ РОБОТИ З НОВИНАМИ ==========
class NewsListView(ListView):
    model = News
    template_name = 'tours/news.html'
    context_object_name = 'news'
    paginate_by = 9
    ordering = ['-created_at']


def consultation_success(request):
    return render(request, 'tours/consultation_success.html')


# ========== ДОДАТКОВІ ФУНКЦІЇ ==========
def get_cities(request):
    from .models import City
    country = request.GET.get('country')
    if country:
        cities = City.objects.filter(country__icontains=country).values('id', 'name')
        return JsonResponse(list(cities), safe=False)
    return JsonResponse([], safe=False)


def popular_tours_api(request):
    tours = Tour.objects.filter(is_popular=True)[:8]
    data = []
    for tour in tours:
        data.append({
            'id': tour.id,
            'title': tour.title,
            'country': tour.country,
            'city': tour.city.name if tour.city else '',
            'price': float(tour.price),
            'image': tour.image.url if tour.image else None,
            'detail_url': f'/tour/{tour.id}/'
        })
    return JsonResponse(data, safe=False)


def tours_by_city(request):
    city = request.GET.get('city')
    if city:
        tours = Tour.objects.filter(departure_city__icontains=city)[:20]
        data = []
        for tour in tours:
            data.append({
                'id': tour.id,
                'title': tour.title,
                'country': tour.country,
                'price': float(tour.price),
                'image': tour.image.url if tour.image else None,
            })
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


def chat_api(request):
    from .gemine_chat import get_gemini_response
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            if not message:
                return JsonResponse({'error': 'Порожнє повідомлення'}, status=400)
            agency_name = "ТурКонструктор"
            if hasattr(request, 'current_agent_site') and request.current_agent_site:
                agency_name = request.current_agent_site.agency_name or agency_name
            response = get_gemini_response(message, request, agency_name)
            return JsonResponse(response)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Некоректний JSON'}, status=400)
    return JsonResponse({'error': 'Метод не підтримується'}, status=405)


def search_otpusk_new(request, slug=None):
    """Нова сторінка результатів пошуку турів (оновлена версія)"""
    geo = request.GET.get('geo', '')
    departure_text = request.GET.get('departure_text', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    duration = request.GET.get('duration', '7')
    auto_search = request.GET.get('auto_search', '1')

    agent_site = getattr(request, 'current_agent_site', None)

    context = {
        'agent_site': agent_site,
        'geo': geo,
        'departure_text': departure_text,
        'date_from': date_from,
        'date_to': date_to,
        'duration': duration,
        'auto_search': auto_search,
    }
    return render(request, 'search_otpusk_new.html', context)


def custom_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')