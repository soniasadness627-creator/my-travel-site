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
from .models import Tour, News, Review, Consultation, Booking
from .forms import ConsultationForm, ReviewForm

User = get_user_model()


# ========== ДОПОМІЖНА ФУНКЦІЯ ДЛЯ ОТРИМАННЯ ВИПАДКОВОГО АГЕНТА ==========
def get_random_agent():
    """Повертає випадкового агента для блоку консультації"""
    agents = User.objects.filter(is_agent=True)
    if agents.exists():
        return random.choice(agents)
    return None


# ========== API ДЛЯ КАЛЕНДАРЯ НИЗЬКИХ ЦІН ==========
def calendar_prices_otpusk(request):
    """
    API для календаря низьких цін, що використовує пошук Otpusk.com
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

            days_in_month = 30
            prices = []
            for day in range(1, days_in_month + 1):
                prices.append(prices_by_day.get(day, None))

            max_price = max([p for p in prices if p is not None], default=50000)
            return JsonResponse({'prices': prices, 'max_price': max_price})
        else:
            return JsonResponse(get_fallback_prices(month, year))
    except Exception as e:
        print(f"Помилка Otpusk API: {e}")
        return JsonResponse(get_fallback_prices(month, year))


def get_fallback_prices(month, year):
    """Заглушка для цін, якщо API не працює"""
    random.seed(year * 12 + month)
    days_in_month = 30
    prices = []
    for day in range(1, days_in_month + 1):
        base_price = random.randint(20000, 80000)
        is_weekend = (day % 7 in [0, 1])
        if is_weekend:
            base_price = int(base_price * 1.3)
        prices.append(base_price)
    max_price = max(prices)
    return {'prices': prices, 'max_price': max_price}


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
    """
    Деталі туру - використовує дані з Otpusk.
    Якщо тур не знайдено в базі, повертає 404.
    """
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


# ========== НОВА СТОРІНКА ДЛЯ ДЕТАЛЬНОГО ПЕРЕГЛЯДУ ТУРУ (БЕЗ ФОРМИ ПОШУКУ) ==========
def tour_detail_otpusk(request, slug=None):
    """
    Сторінка детального перегляду туру (без форми пошуку)
    """
    agent_site = getattr(request, 'current_agent_site', None)
    context = {
        'agent_site': agent_site,
        'random_agent': get_random_agent(),
    }
    return render(request, 'tours/tour_detail_otpusk.html', context)


# ========== AJAX ОБРОБКА БРОНЮВАННЯ (Booking) ==========
@csrf_exempt
@require_http_methods(["POST"])
def booking_ajax(request, slug=None):
    """
    AJAX-обробка форми бронювання (зберігається в Booking)
    """
    try:
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        tour_name = request.POST.get('tour_name', '').strip()
        tour_price = request.POST.get('tour_price', '').strip()
        tour_dates = request.POST.get('tour_dates', '').strip()
        country_code = request.POST.get('country_code', '+380')

        # Валідація
        if not name:
            return JsonResponse({'success': False, 'error': "Введіть ваше ім'я"})
        if not phone:
            return JsonResponse({'success': False, 'error': "Введіть номер телефону"})
        if not email:
            return JsonResponse({'success': False, 'error': "Введіть email"})

        # Очищуємо телефон
        phone_clean = re.sub(r'[^0-9]', '', phone)
        if len(phone_clean) < 9:
            return JsonResponse({'success': False, 'error': "Введіть коректний номер телефону (мінімум 9 цифр)"})

        full_phone = f"{country_code}{phone_clean}"

        # Формуємо повідомлення
        full_message = f"Тур: {tour_name}\n"
        if tour_price:
            full_message += f"Ціна: {tour_price}\n"
        if tour_dates:
            full_message += f"Дати: {tour_dates}\n"
        if message:
            full_message += f"Коментар клієнта: {message}"

        # Створюємо заявку (tour=None, тому що це бронювання з Otpusk)
        booking = Booking.objects.create(
            tour=None,  # ← ОСЬ ГОЛОВНЕ ВИПРАВЛЕННЯ
            name=name,
            phone=full_phone,
            email=email,
            message=full_message
        )

        print(f"✅ Нова заявка на бронювання: {name} - {full_phone} - {email} (ID: {booking.id})")

        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Наш менеджер зв\'яжеться з вами найближчим часом.'
        })

    except Exception as e:
        print(f"❌ ПОМИЛКА: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ========== AJAX ОБРОБКА КОНСУЛЬТАЦІЇ ==========
@csrf_exempt
@require_http_methods(["POST"])
def consultation_ajax(request, slug=None):
    """
    AJAX-обробка форми консультації (без перенаправлення)
    """
    try:
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        comment = request.POST.get('comment', '').strip()
        country_code = request.POST.get('country_code', '+380')

        # Валідація
        if not name:
            return JsonResponse({'success': False, 'error': "Введіть ваше ім'я"})
        if not phone:
            return JsonResponse({'success': False, 'error': "Введіть номер телефону"})

        # Очищуємо телефон від нецифрових символів
        phone_clean = re.sub(r'[^0-9]', '', phone)
        if len(phone_clean) < 9:
            return JsonResponse({'success': False, 'error': "Введіть коректний номер телефону (мінімум 9 цифр)"})

        # Формуємо повний номер
        full_phone = f"{country_code}{phone_clean}"

        # Створюємо заявку
        consultation = Consultation.objects.create(
            name=name,
            phone=full_phone,
            comment=comment
        )

        # Якщо є агентський сайт, прив'язуємо заявку до агента
        if hasattr(request, 'current_agent_site') and request.current_agent_site:
            consultation.agent = request.current_agent_site.user
            consultation.save()
            print(f"✅ Заявка прив'язана до агента: {request.current_agent_site.user.username}")
        elif slug:
            # Якщо slug передано, але current_agent_site не встановлено
            try:
                from .models.agent_site import AgentSite
                agent_site = AgentSite.objects.filter(slug=slug).first()
                if agent_site:
                    consultation.agent = agent_site.user
                    consultation.save()
                    print(f"✅ Заявка прив'язана до агента (за slug): {agent_site.user.username}")
            except Exception as e:
                print(f"⚠️ Не вдалося прив'язати агента за slug: {e}")

        print(f"✅ Нова заявка на консультацію: {name} - {full_phone}")

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
    """Сторінка успішного відправлення заявки (для звичайної форми)"""
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
    """API для отримання популярних турів (для каруселі)"""
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