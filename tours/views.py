import requests
import json
import random
import re
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
from .models import Tour, News, Review, Consultation, Booking, HotelReview, PriceCalendar
from .forms import ConsultationForm, ReviewForm

User = get_user_model()


# ========== ДОПОМІЖНА ФУНКЦІЯ ДЛЯ ОТРИМАННЯ ВИПАДКОВОГО АГЕНТА ==========
def get_random_agent():
    """Повертає випадкового агента для блоку консультації"""
    agents = User.objects.filter(is_agent=True)
    if agents.exists():
        return random.choice(agents)
    return None


# ========== API ДЛЯ КАЛЕНДАРЯ НИЗЬКИХ ЦІН (OTPUSK) ==========
def calendar_prices_otpusk(request):
    """
    API для календаря низьких цін, що використовує пошук Otpusk.com
    (Залишено для зворотної сумісності)
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

    otpusk_url = "https://export.otpusk.com/api/2.4/search"
    params = {
        'country': country,
        'departure': departure or 'Київ',
        'date_from': f"{year}-{month:02d}-01",
        'date_to': f"{year}-{month:02d}-28",
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
                    start_date = tour.get('start_date')
                    if start_date:
                        day = int(start_date.split('-')[2])
                        price = tour.get('price')
                        if day not in prices_by_day or price < prices_by_day[day]:
                            prices_by_day[day] = price

            # Визначаємо кількість днів у місяці
            if month == 12:
                last_day = 31
            else:
                next_month = datetime(year, month + 1, 1)
                last_day = (next_month - timedelta(days=1)).day

            prices = []
            for day in range(1, last_day + 1):
                prices.append(prices_by_day.get(day, None))

            max_price = max([p for p in prices if p is not None], default=50000)
            return JsonResponse({'prices': prices, 'max_price': max_price})
        else:
            return JsonResponse(get_fallback_prices(month, year))
    except Exception as e:
        print(f"Помилка Otpusk API: {e}")
        return JsonResponse(get_fallback_prices(month, year))


# ========== НОВЕ API ДЛЯ КАЛЕНДАРЯ (ПРЯМЕ ПІДКЛЮЧЕННЯ ДО OTPUSK) ==========
def calendar_prices_from_otpusk(request):
    """
    API для календаря низьких цін, що отримує реальні ціни безпосередньо з Otpusk.com
    Використовується на головній сторінці для календаря
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

    # Формуємо перший і останній день місяця
    if month == 12:
        start_date = f"{year}-12-01"
        end_date = f"{year + 1}-01-01"
        last_day = 31
    else:
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month + 1:02d}-01"
        next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day

    otpusk_url = "https://export.otpusk.com/api/2.4/search"
    params = {
        'country': country,
        'departure': departure or 'Кишинев',
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
                    if start_date_str:
                        try:
                            tour_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                            day = tour_date.day
                            price = tour.get('price')
                            if price and price > 0:
                                price_int = int(price)
                                if day not in prices_by_day or price_int < prices_by_day[day]:
                                    prices_by_day[day] = price_int
                        except Exception as e:
                            print(f"Помилка парсингу дати: {e}")
                            pass

            # Заповнюємо масив цін
            prices = []
            for day in range(1, last_day + 1):
                prices.append(prices_by_day.get(day, None))

            max_price = max([p for p in prices if p is not None], default=50000)
            print(f"📊 Календар для {country} ({year}-{month}): знайдено {len([p for p in prices if p])} днів з цінами")
            return JsonResponse({'prices': prices, 'max_price': max_price})
        else:
            print(f"❌ Помилка Otpusk API: статус {response.status_code}")
            return JsonResponse({'error': 'Otpusk API error'}, status=response.status_code)
    except Exception as e:
        print(f"❌ Помилка Otpusk API: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ========== НОВЕ API ДЛЯ РЕАЛЬНИХ ЦІН З OTPUSK (ГОЛОВНЕ) ==========
def calendar_prices_real(request):
    """
    API для отримання реальних мінімальних цін на тури з Otpusk.com
    Використовується для календаря низьких цін на головній сторінці
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

    # Мапи для конвертації назв (Otpusk API працює з латиницею)
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
        'Дніпро': 'Dnipro',
    }

    api_country = country_map.get(country, country)
    api_departure = departure_map.get(departure, departure or 'Chisinau')

    # Визначаємо діапазон дат
    if month == 12:
        start_date = f"{year}-12-01"
        end_date = f"{year + 1}-01-01"
        from datetime import date as date_type
        days_in_month = 31
    else:
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month + 1:02d}-01"
        from datetime import date as date_type
        days_in_month = (date_type(year, month + 1, 1) - date_type(year, month, 1)).days

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
        print(f"🔍 Запит до Otpusk: {params}")
        response = requests.get(otpusk_url, params=params, timeout=60)

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

            # Заповнюємо масив цін
            prices = []
            for day in range(1, days_in_month + 1):
                prices.append(prices_by_day.get(day, None))

            found_days = len([p for p in prices if p is not None])
            print(f"✅ Знайдено ціни для {found_days} днів у {country} ({year}-{month})")

            # Якщо знайдено хоча б одну ціну - повертаємо їх
            if found_days > 0:
                max_price = max([p for p in prices if p is not None], default=50000)
                return JsonResponse({'prices': prices, 'max_price': max_price})
            else:
                # Якщо цін немає - повертаємо заглушку
                print(f"⚠️ Не знайдено цін для {country}, використовуємо заглушку")
                return JsonResponse(get_fallback_prices(month, year))
        else:
            print(f"❌ Помилка Otpusk API: статус {response.status_code}")
            return JsonResponse(get_fallback_prices(month, year))

    except Exception as e:
        print(f"❌ Помилка запиту до Otpusk API: {e}")
        return JsonResponse(get_fallback_prices(month, year))


def get_fallback_prices(month, year):
    """Заглушка для цін, якщо API не працює"""
    random.seed(year * 12 + month)
    # Визначаємо кількість днів у місяці
    if month == 12:
        days_in_month = 31
    else:
        next_month = datetime(year, month + 1, 1)
        days_in_month = (next_month - timedelta(days=1)).day

    prices = []
    for day in range(1, days_in_month + 1):
        base_price = random.randint(20000, 80000)
        is_weekend = (day % 7 in [0, 1, 6])
        if is_weekend:
            base_price = int(base_price * 1.3)
        prices.append(base_price)
    max_price = max(prices)
    return {'prices': prices, 'max_price': max_price}


# ========== НОВЕ API ДЛЯ КАЛЕНДАРЯ НИЗЬКИХ ЦІН (З БАЗИ ДАНИХ) ==========
def calendar_prices_from_db(request):
    """API для отримання реальних цін з бази даних"""
    country = request.GET.get('country')
    year = request.GET.get('year')
    month = request.GET.get('month')
    departure = request.GET.get('departure')  # місто вильоту

    if not all([country, year, month]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        return JsonResponse({'error': 'Invalid year/month'}, status=400)

    # Формуємо діапазон дат місяця
    from datetime import date
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Шукаємо тури за параметрами
    tours = Tour.objects.filter(
        country__icontains=country,
        departure_city__icontains=departure
    )

    # Отримуємо мінімальні ціни на кожну дату
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

    # Заповнюємо всі дні місяця
    days_in_month = (end_date - start_date).days
    prices = []
    for day in range(1, days_in_month + 1):
        prices.append(prices_by_day.get(day, None))

    max_price = max([p for p in prices if p is not None], default=50000)

    return JsonResponse({'prices': prices, 'max_price': max_price})


# ========== ГОЛОВНА СТОРІНКА ==========
def home(request):
    """
    Головна сторінка з пошуком Otpusk та календарем низьких цін
    """
    agent_site = getattr(request, 'current_agent_site', None)

    context = {
        'agent_site': agent_site,
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
    """Сторінка результатів пошуку Otpusk.com (БЕЗ блоку консультації)"""
    agent_site = getattr(request, 'current_agent_site', None)
    context = {'agent_site': agent_site}
    return render(request, 'tours/search_results_otpusk.html', context)


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


# ========== API ДЛЯ ВІДГУКІВ (З ПРИВ'ЯЗКОЮ ДО АГЕНТА) ==========
@csrf_exempt
@require_http_methods(["GET", "POST"])
def hotel_reviews_api(request, slug=None):
    """
    API для відгуків про готелі
    GET - отримання відгуків (тільки опубліковані)
    POST - збереження нового відгуку з прив'язкою до агента
    """

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
                except Exception as e:
                    print(f"Помилка визначення агента за slug: {e}")

            if not agent and hasattr(request, 'current_agent_site') and request.current_agent_site:
                agent = request.current_agent_site.user

            existing_review = HotelReview.objects.filter(hid=hid, guest_name=guest_name).first()

            if existing_review:
                existing_review.rating = rating
                existing_review.comment = comment
                existing_review.created_at = timezone.now()
                if agent and not existing_review.agent:
                    existing_review.agent = agent
                existing_review.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Ваш відгук оновлено!'
                })
            else:
                new_review = HotelReview.objects.create(
                    hid=hid,
                    oid=oid,
                    guest_name=guest_name,
                    rating=rating,
                    comment=comment,
                    agent=agent
                )
                return JsonResponse({
                    'success': True,
                    'message': 'Дякуємо за ваш відгук!'
                })

        except Exception as e:
            print(f"Помилка збереження відгуку: {e}")
            return JsonResponse({'error': str(e), 'success': False}, status=500)


# ========== СТОРІНКА ДЛЯ ДЕТАЛЬНОГО ПЕРЕГЛЯДУ ТУРУ ==========

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


# ========== AJAX ОБРОБКА БРОНЮВАННЯ (Booking) ==========
@csrf_exempt
@require_http_methods(["POST"])
def booking_ajax(request, slug=None):
    print("=" * 50)
    print("🚀 booking_ajax ВИКЛИКАНО!")
    print(f"slug: {slug}")
    print(f"POST data: {request.POST}")
    print("=" * 50)

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
            tour=None,
            name=name,
            phone=full_phone,
            email=email,
            message=full_message
        )

        print(f"✅ Booking створено! ID={booking.id}")

        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Наш менеджер зв\'яжеться з вами найближчим часом.'
        })

    except Exception as e:
        print(f"❌ ПОМИЛКА: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== AJAX ОБРОБКА КОНСУЛЬТАЦІЇ ==========
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

        consultation = Consultation.objects.create(
            name=name,
            phone=full_phone,
            comment=comment
        )

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
            except Exception as e:
                print(f"⚠️ Не вдалося прив'язати агента за slug: {e}")

        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Наш менеджер зв\'яжеться з вами найближчим часом.'
        })

    except Exception as e:
        print(f"❌ Помилка при збереженні заявки: {e}")
        return JsonResponse({'success': False, 'error': 'Сталася помилка. Спробуйте пізніше.'}, status=500)


# ========== КЛАСИ ДЛЯ РОБОТИ З НОВИНАМИ ==========

class NewsListView(ListView):
    """Список новин"""
    model = News
    template_name = 'tours/news.html'
    context_object_name = 'news'
    paginate_by = 9
    ordering = ['-created_at']


def consultation_success(request):
    """Сторінка успішного відправлення заявки"""
    return render(request, 'tours/consultation_success.html')


# ========== ДОДАТКОВІ ФУНКЦІЇ ==========

def get_cities(request):
    """AJAX-функція для отримання міст за країною"""
    from .models import City
    country = request.GET.get('country')
    if country:
        cities = City.objects.filter(country__icontains=country).values('id', 'name')
        return JsonResponse(list(cities), safe=False)
    return JsonResponse([], safe=False)


def popular_tours_api(request):
    """API для отримання популярних турів"""
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
    """API для отримання турів за містом вильоту"""
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
    """API для чат-бота"""
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


def custom_logout(request):
    """Кастомний вихід з системи"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')