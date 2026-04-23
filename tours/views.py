from .forms import ConsultationForm, ReviewForm, PriceSearchForm, GuestReviewForm
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from django.db.models import Exists, OuterRef, Q, Count, Avg, Min, ExpressionWrapper, F, DurationField, Case, When, \
    Value, Subquery
from .gemini_chat import get_gemini_response
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from django.utils import timezone
import os

from django.conf import settings
from .models import TourPriceByTourists

from collections import defaultdict
import random
import json
from django.contrib.auth import get_user_model
from .gemini_chat import get_gemini_response

User = get_user_model()

from .models import (
    Tour, Booking, News, TourImage, Consultation, Review,
    PriceOption, PriceCalendar, Amenity, City, DepartureCity, PopularDestination,
    CountryInfo
)
from django.contrib.auth import logout
from django.shortcuts import redirect


def custom_logout(request):
    logout(request)
    return redirect('home')


# ---------- ДОПОМІЖНА ФУНКЦІЯ ДЛЯ ОТРИМАННЯ КОЛЬОРІВ АГЕНТА ----------
def get_agent_colors(request):
    """Повертає кольори агента для використання в шаблонах"""
    agent_site = getattr(request, 'current_agent_site', None)
    if agent_site:
        return {
            'primary_color': agent_site.primary_color or '#086745',
            'secondary_color': agent_site.secondary_color or '#02432c',
            'primary_dark': agent_site.secondary_color or '#02432c',
            'primary_light': agent_site.get_primary_light() if hasattr(agent_site, 'get_primary_light') else '#2a6b5c',
            'primary_lighter': agent_site.get_primary_lighter() if hasattr(agent_site,
                                                                           'get_primary_lighter') else '#cbf6ec',
        }
    return {
        'primary_color': '#086745',
        'secondary_color': '#02432c',
        'primary_dark': '#02432c',
        'primary_light': '#2a6b5c',
        'primary_lighter': '#cbf6ec',
    }


# ---------- ДОПОМІЖНА ФУНКЦІЯ ДЛЯ ФІЛЬТРАЦІЇ ТУРІВ ----------
def filter_tours_by_agent_site(queryset, request):
    agent_site = getattr(request, 'current_agent_site', None)
    if agent_site:
        if agent_site.show_superadmin_tours:
            return queryset.filter(models.Q(author__is_superuser=True) | models.Q(author=agent_site.user))
        else:
            return queryset.filter(author=agent_site.user)
    return queryset


# ---------- ДОПОМІЖНА ФУНКЦІЯ ДЛЯ ОТРИМАННЯ ВИПАДКОВОГО АГЕНТА ----------
def get_random_agent():
    agents = User.objects.filter(is_agent=True)
    return random.choice(agents) if agents.exists() else None


# ---------------------------------------------------------------


# -------------------------
# Головна сторінка - список турів
# -------------------------
class TourListView(ListView):
    model = Tour
    template_name = 'tours/home.html'
    context_object_name = 'tours'
    paginate_by = 9

    def dispatch(self, request, *args, **kwargs):
        # Перевіряємо, чи це головна сторінка адміністратора (/home/)
        if request.path == '/home/':
            # Доступ тільки для суперадміна
            if not request.user.is_authenticated or not request.user.is_superuser:
                return redirect('landing:index')  # Перенаправляємо на лендинг
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Tour.objects.all().order_by('-created_at')

        search = self.request.GET.get('search')
        if search:
            words = search.strip().split()
            query = Q()
            for word in words:
                if len(word) < 2:
                    continue
                query |= Q(title__icontains=word)
                query |= Q(description__icontains=word)
                query |= Q(country__icontains=word)
            queryset = queryset.filter(query)

        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            try:
                min_price = Decimal(min_price.replace(',', '.'))
                queryset = queryset.filter(price__gte=min_price)
            except (InvalidOperation, ValueError):
                pass
        if max_price:
            try:
                max_price = Decimal(max_price.replace(',', '.'))
                queryset = queryset.filter(price__lte=max_price)
            except (InvalidOperation, ValueError):
                pass

        queryset = filter_tours_by_agent_site(queryset, self.request)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        colors = get_agent_colors(self.request)
        context.update(colors)

        agent_site = getattr(self.request, 'current_agent_site', None)
        if agent_site:
            context['agent_site'] = agent_site
            context['hero_title'] = agent_site.hero_title
            context['hero_subtitle'] = agent_site.hero_subtitle
            context['hero_background_url'] = agent_site.hero_background.url if agent_site.hero_background else None
            context['top_logo'] = agent_site.top_logo
            context['bottom_logo'] = agent_site.bottom_logo
            context['enlarge_logo'] = agent_site.enlarge_logo
            context['agency_name'] = agent_site.agency_name
            context['hide_news'] = not agent_site.show_news
            context['show_operator_logos'] = agent_site.show_operator_logos
        else:
            context['hero_title'] = "Ваша подорож починається тут"
            context['hero_subtitle'] = "Знайдіть ідеальний тур за лічені хвилини"
            context['hero_background_url'] = None
            context['top_logo'] = None
            context['bottom_logo'] = None
            context['enlarge_logo'] = False
            context['agency_name'] = ''
            context['hide_news'] = False
            context['show_operator_logos'] = False

        context['search'] = self.request.GET.get('search', '')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')

        tour_countries = list(Tour.objects.values_list('country', flat=True).distinct().order_by('country'))
        city_countries = list(City.objects.values_list('country', flat=True).distinct().order_by('country'))
        all_countries = sorted(set(tour_countries + city_countries))
        context['countries'] = all_countries

        departure_cities = DepartureCity.objects.all().order_by('country', 'name')
        departure_groups = []
        current_country = None
        group = None
        for city in departure_cities:
            if city.country != current_country:
                if group:
                    departure_groups.append(group)
                group = {'country': city.country, 'cities': []}
                current_country = city.country
            group['cities'].append({
                'name': city.name,
                'transport': city.get_transport_display()
            })
        if group:
            departure_groups.append(group)
        context['departure_groups'] = departure_groups

        available_dates = PriceOption.objects.filter(
            is_available=True,
            departure_date__isnull=False
        ).values_list('departure_date', flat=True).distinct().order_by('departure_date')
        today = timezone.now().date()
        available_dates = [d for d in available_dates if d >= today]
        context['available_dates_json'] = [d.strftime('%Y-%m-%d') for d in available_dates]

        context['low_price_countries'] = [
            'Єгипет', 'Туреччина', 'ОАЕ', 'Шрі Ланка', 'Іспанія',
            'Мальдіви', 'Кіпр', 'Грузія', 'Чехія', 'Індонезія', 'Маврикій'
        ]

        viewed_tours_ids = self.request.session.get('viewed_tours', [])
        recommended_tours_qs = None
        if viewed_tours_ids:
            last_tour = Tour.objects.filter(pk=viewed_tours_ids[0]).first()
            if last_tour:
                qs = Tour.objects.filter(country=last_tour.country).exclude(pk=last_tour.pk).order_by('-created_at')
                if last_tour.departure_city:
                    qs = qs.filter(departure_city=last_tour.departure_city)
                qs = qs.annotate(
                    avg_rating=Avg('reviews__rating'),
                    reviews_count=Count('reviews')
                )
                recommended_tours_qs = qs
        if not recommended_tours_qs:
            recommended_tours_qs = Tour.objects.all().order_by('-created_at').annotate(
                avg_rating=Avg('reviews__rating'),
                reviews_count=Count('reviews')
            )
        recommended_tours_qs = filter_tours_by_agent_site(recommended_tours_qs, self.request)
        context['recommended_tours'] = recommended_tours_qs[:9]

        fixed_cities = [
            'Київ', 'Кишинів', 'Варшава', 'Жешув', 'Краків',
            'Вроцлав', 'Катовіце', 'Будапешт', 'Прага', 'Берлін',
            'Ясси', 'Сучава', 'Відень'
        ]
        context['departure_cities'] = fixed_cities

        first_city = fixed_cities[0] if fixed_cities else None
        countries_by_city = []
        if first_city:
            tours_qs = Tour.objects.filter(departure_city=first_city)

            if agent_site:
                if agent_site.show_superadmin_tours:
                    tours_qs = tours_qs.filter(models.Q(author__is_superuser=True) | models.Q(author=agent_site.user))
                else:
                    tours_qs = tours_qs.filter(author=agent_site.user)
            else:
                tours_qs = tours_qs

            tours_qs = tours_qs.filter(
                country__isnull=False,
                country__gt='',
                price__isnull=False,
                price__gt=0,
                start_date__isnull=False
            )

            if tours_qs.exists():
                countries_dict = {}
                for tour in tours_qs:
                    country = tour.country
                    if country and country.strip():
                        if country not in countries_dict:
                            countries_dict[country] = {
                                'country': country,
                                'image_url': tour.image.url if tour.image else '',
                                'min_price': tour.price,
                                'closest_date': tour.start_date,
                                'avg_rating': tour.avg_rating if hasattr(tour, 'avg_rating') else None,
                            }
                        else:
                            if tour.price < countries_dict[country]['min_price']:
                                countries_dict[country]['min_price'] = tour.price
                            if tour.start_date < countries_dict[country]['closest_date']:
                                countries_dict[country]['closest_date'] = tour.start_date

                filtered_countries = []
                for country_data in countries_dict.values():
                    if country_data['min_price'] and country_data['closest_date']:
                        country_data['closest_date'] = country_data['closest_date'].strftime('%d.%m')
                        country_data['min_price'] = float(country_data['min_price'])
                        filtered_countries.append(country_data)

                countries_by_city = filtered_countries
            else:
                countries_by_city = []
        context['countries_by_city'] = countries_by_city

        popular_tours_qs = Tour.objects.filter(is_popular=True).annotate(
            avg_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews')
        )
        popular_tours_qs = filter_tours_by_agent_site(popular_tours_qs, self.request)
        context['popular_tours'] = popular_tours_qs.order_by('?')[:6]

        popular_destinations = []
        for dest in PopularDestination.objects.all():
            tours_for_country = filter_tours_by_agent_site(Tour.objects.filter(country=dest.country), self.request)
            min_price = tours_for_country.aggregate(Min('price'))['price__min']
            cities = City.objects.filter(
                country=dest.country,
                tour__in=tours_for_country
            ).annotate(
                tours_count=Count('tour')
            ).order_by('-tours_count')[:4]
            if tours_for_country.exists():
                popular_destinations.append({
                    'country': dest.country,
                    'image_url': dest.image.url,
                    'min_price': min_price,
                    'cities': cities,
                })
        context['popular_destinations'] = popular_destinations

        context['random_agent'] = get_random_agent()

        if agent_site:
            context['debug_show_superadmin'] = agent_site.show_superadmin_tours
        else:
            context['debug_show_superadmin'] = None

        if agent_site:
            context['user_tours_exists'] = Tour.objects.filter(author=agent_site.user).exists()
        else:
            context['user_tours_exists'] = True

        return context

    def post(self, request, *args, **kwargs):
        if 'consultation_submit' in request.POST:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            country_code = request.POST.get('country_code', '')
            full_phone = country_code + phone if phone else ''

            if name and full_phone:
                agent_site = getattr(request, 'current_agent_site', None)
                agent = agent_site.user if agent_site else None
                try:
                    Consultation.objects.create(
                        name=name,
                        phone=full_phone,
                        comment="Заявка з головної сторінки",
                        agent=agent
                    )
                except Exception as e:
                    print(f"ПОМИЛКА створення консультації: {e}")
                messages.success(request, 'Ваш запит прийнято. Ми зв\'яжемося з вами найближчим часом.')
                referer = request.META.get('HTTP_REFERER', '/')
                return redirect(referer)
            else:
                messages.error(request, 'Будь ласка, заповніть ім\'я та телефон.')
                referer = request.META.get('HTTP_REFERER', '/')
                return redirect(referer)

        return self.get(request, *args, **kwargs)


# -------------------------
# Деталі туру
# -------------------------
def tour_detail(request, pk):
    tour = get_object_or_404(Tour, pk=pk)
    agent_site = getattr(request, 'current_agent_site', None)

    # ОБРОБКА POST ЗАПИТІВ (бронювання та відгуки)
    if request.method == 'POST':
        print("=== ОТРИМАНО POST ЗАПИТ ===")
        print("POST data:", request.POST)

        # Визначаємо is_ajax на початку
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Перевіряємо, чи це запит на бронювання
        if 'booking_submit' in request.POST or 'name' in request.POST:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            message = request.POST.get('message', '')

            # Валідація
            if not all([name, phone, email]):
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Будь ласка, заповніть всі обов\'язкові поля'})
                messages.error(request, 'Будь ласка, заповніть всі обов\'язкові поля')
                if agent_site:
                    return redirect('agent_tour_detail', slug=agent_site.slug, pk=tour.pk)
                return redirect('tour_detail', pk=tour.pk)

            # ЗБЕРІГАЄМО БРОНЮВАННЯ В БАЗУ
            try:
                booking = Booking.objects.create(
                    tour=tour,
                    name=name,
                    phone=phone,
                    email=email,
                    message=message
                )
                print(f"=== БРОНЮВАННЯ СТВОРЕНО: ID={booking.id} ===")
            except Exception as e:
                print(f"=== ПОМИЛКА ПРИ ЗБЕРЕЖЕННІ: {e} ===")
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Помилка при збереженні. Спробуйте ще раз.'})
                messages.error(request, 'Помилка при збереженні. Спробуйте ще раз.')
                if agent_site:
                    return redirect('agent_tour_detail', slug=agent_site.slug, pk=tour.pk)
                return redirect('tour_detail', pk=tour.pk)

            # УСПІШНА ВІДПОВІДЬ
            if is_ajax:
                return JsonResponse({'success': True})

            messages.success(request, 'Дякуємо за заявку! Наш менеджер зв\'яжеться з вами найближчим часом.')
            if agent_site:
                return redirect('agent_tour_detail', slug=agent_site.slug, pk=tour.pk)
            return redirect('tour_detail', pk=tour.pk)

        # Перевіряємо, чи це запит на відгук
        elif 'review_submit' in request.POST:
            if agent_site:
                redirect_url = reverse('agent_tour_detail', args=[agent_site.slug, tour.pk])
            else:
                redirect_url = reverse('tour_detail', args=[tour.pk])

            if request.user.is_authenticated:
                existing_review = Review.objects.filter(tour=tour, user=request.user).first()

                if existing_review:
                    form = ReviewForm(request.POST, instance=existing_review)
                    if form.is_valid():
                        review = form.save(commit=False)
                        review.tour = tour
                        review.user = request.user
                        review.save()
                        messages.success(request, 'Ваш відгук оновлено!')
                    else:
                        messages.error(request, 'Помилка при оновленні відгуку')
                else:
                    form = ReviewForm(request.POST)
                    if form.is_valid():
                        review = form.save(commit=False)
                        review.tour = tour
                        review.user = request.user
                        review.save()
                        messages.success(request, 'Дякуємо за ваш відгук!')
                    else:
                        messages.error(request, 'Помилка при збереженні відгуку')
            else:
                guest_name = request.POST.get('guest_name', '').strip()
                rating = request.POST.get('rating')
                comment = request.POST.get('comment', '').strip()

                if not guest_name:
                    messages.error(request, 'Будь ласка, введіть ваше ім\'я')
                    return redirect(redirect_url)

                if not rating or not comment:
                    messages.error(request, 'Будь ласка, заповніть всі поля')
                    return redirect(redirect_url)

                existing_review = Review.objects.filter(tour=tour, guest_name=guest_name).first()

                if existing_review:
                    existing_review.rating = int(rating)
                    existing_review.comment = comment
                    existing_review.save()
                    messages.success(request, f'Дякуємо {guest_name}, ваш відгук оновлено!')
                else:
                    Review.objects.create(
                        tour=tour,
                        guest_name=guest_name,
                        rating=int(rating),
                        comment=comment,
                        user=None
                    )
                    messages.success(request, f'Дякуємо {guest_name}, ваш відгук збережено!')

            return redirect(redirect_url)

        # Якщо це не бронювання і не відгук - повертаємо помилку
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Невідомий тип запиту'})

    # ========== ВЕСЬ ІНШИЙ КОД ДЛЯ GET ЗАПИТІВ ==========

    viewed_tours = request.session.get('viewed_tours', [])
    if tour.pk in viewed_tours:
        viewed_tours.remove(tour.pk)
    viewed_tours.insert(0, tour.pk)
    request.session['viewed_tours'] = viewed_tours[:5]

    gallery_images = tour.gallery.all()
    reviews = tour.reviews.all().select_related('user').order_by('-created_at')
    user_review_exists = False
    if request.user.is_authenticated:
        user_review_exists = Review.objects.filter(tour=tour, user=request.user).exists()

    week_offset = int(request.GET.get('week_offset', 0))
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_date = start_of_week + timedelta(weeks=week_offset)
    end_date = start_date + timedelta(days=6)

    calendar_entries = tour.price_calendar.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date', 'duration')

    calendar_data = {}
    durations = set()
    for entry in calendar_entries:
        durations.add(entry.duration)
        if entry.duration not in calendar_data:
            calendar_data[entry.duration] = {}
        calendar_data[entry.duration][entry.date] = entry.price

    dates = [start_date + timedelta(days=i) for i in range(7)]
    durations = sorted(durations)

    all_price_options = tour.price_options.filter(is_available=True).order_by('departure_date', 'price')
    price_options = all_price_options[:3]
    search_form = PriceSearchForm(request.GET or None)

    available_dates = all_price_options.filter(departure_date__isnull=False).values_list('departure_date',
                                                                                         flat=True).distinct().order_by(
        'departure_date')
    available_dates_json = [d.strftime('%Y-%m-%d') for d in available_dates if d is not None]

    if search_form.is_valid():
        filters = {}
        if search_form.cleaned_data.get('start_date'):
            filters['departure_date'] = search_form.cleaned_data['start_date']
        if search_form.cleaned_data.get('duration_min'):
            filters['duration__gte'] = search_form.cleaned_data['duration_min']
        if search_form.cleaned_data.get('duration_max'):
            filters['duration__lte'] = search_form.cleaned_data['duration_max']
        filtered = all_price_options.filter(**filters)
        price_options = filtered[:3] if filtered.exists() else PriceOption.objects.none()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if 'week_offset' in request.GET:
            return render(request, 'tours/_price_calendar.html', {
                'calendar_data': calendar_data,
                'durations': durations,
                'dates': dates,
                'start_date': start_date,
                'end_date': end_date,
                'week_offset': week_offset,
            })
        else:
            return render(request, 'tours/_price_results.html', {
                'price_options': price_options,
                'search_form': search_form,
            })

    # Обробка відгуків для GET запиту (створення форми)
    if request.user.is_authenticated:
        review_form = ReviewForm()
    else:
        review_form = GuestReviewForm()

    avg_rating = None
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)
        avg_rating = round(avg_rating, 1)

    similar_tours = filter_tours_by_agent_site(
        Tour.objects.exclude(pk=tour.pk).annotate(reviews_count=Count('reviews')),
        request
    ).order_by('?')[:10]

    price_range_min = tour.price * Decimal('0.8')
    price_range_max = tour.price * Decimal('1.2')
    price_similar_tours = filter_tours_by_agent_site(
        Tour.objects.filter(price__gte=price_range_min, price__lte=price_range_max).exclude(pk=tour.pk).annotate(
            reviews_count=Count('reviews')),
        request
    ).order_by('?')[:10]

    beach_amenity_ids = list(Amenity.objects.filter(category__name__icontains='пляж').values_list('id', flat=True))
    if not beach_amenity_ids:
        try:
            beach_amenity_ids = list(Amenity.objects.filter(name__name__icontains='пляж').values_list('id', flat=True))
        except:
            beach_amenity_ids = []

    if beach_amenity_ids:
        beach_similar_tours = filter_tours_by_agent_site(
            Tour.objects.exclude(pk=tour.pk).filter(amenities__id__in=beach_amenity_ids).distinct().annotate(
                reviews_count=Count('reviews')),
            request
        ).order_by('?')[:10]
    else:
        beach_similar_tours = Tour.objects.none()

    colors = get_agent_colors(request)

    context = {
        'tour': tour,
        'gallery_images': gallery_images,
        'reviews': reviews,
        'review_form': review_form,
        'map_url': tour.map_url,
        'avg_rating': avg_rating,
        'price_options': price_options,
        'search_form': search_form,
        'available_dates_json': available_dates_json,
        'calendar_data': calendar_data,
        'durations': durations,
        'dates': dates,
        'start_date': start_date,
        'end_date': end_date,
        'week_offset': week_offset,
        'similar_tours': similar_tours,
        'price_similar_tours': price_similar_tours,
        'beach_similar_tours': beach_similar_tours,
        'random_agent': get_random_agent(),
        'agent_site': agent_site,
        'user_review_exists': user_review_exists,
    }
    context.update(colors)

    return render(request, 'tours/tour_detail.html', context)

# -------------------------
# ВСІ ВІДГУКИ
# -------------------------
def tour_reviews(request, pk):
    tour = get_object_or_404(Tour, pk=pk)
    agent_site = getattr(request, 'current_agent_site', None)
    reviews = tour.reviews.all().select_related('user').order_by('-created_at')
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    colors = get_agent_colors(request)

    context = {
        'tour': tour,
        'page_obj': page_obj,
        'agent_site': agent_site,
    }
    context.update(colors)

    return render(request, 'tours/tour_reviews.html', context)


# -------------------------
# Кабінет агента
# -------------------------
class AgentDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Tour
    template_name = 'tours/dashboard.html'
    context_object_name = 'my_tours'

    def get_queryset(self):
        return Tour.objects.filter(author=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bookings'] = Booking.objects.filter(
            tour__author=self.request.user
        ).select_related('tour').order_by('-created_at')
        return context

    def test_func(self):
        return self.request.user.is_agent


# -------------------------
# Створення туру
# -------------------------
class TourCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Tour
    fields = [
        'title', 'description', 'country', 'city', 'price',
        'start_date', 'end_date', 'image', 'map_url',
        'departure_city', 'transport',
        'duration', 'room_type', 'meal_type'
    ]
    template_name = 'tours/tour_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_agent

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


# -------------------------
# Редагування туру
# -------------------------
class TourUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tour
    fields = [
        'title', 'description', 'country', 'city', 'price',
        'start_date', 'end_date', 'image', 'map_url',
        'departure_city', 'transport',
        'duration', 'room_type', 'meal_type'
    ]
    template_name = 'tours/tour_form.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        tour = self.get_object()
        return self.request.user == tour.author

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


# -------------------------
# Видалення туру
# -------------------------
class TourDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Tour
    template_name = 'tours/tour_confirm_delete.html'
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        tour = self.get_object()
        return self.request.user == tour.author


# -------------------------
# Новини
# -------------------------
class NewsListView(ListView):
    model = News
    template_name = "tours/news.html"
    context_object_name = "news"
    ordering = ['-created_at']
    paginate_by = 6

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent_site = getattr(self.request, 'current_agent_site', None)
        context['agent_site'] = agent_site
        colors = get_agent_colors(self.request)
        context.update(colors)
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        agent_site = getattr(self.request, 'current_agent_site', None)
        if agent_site:
            if agent_site.show_superadmin_tours:
                queryset = queryset.filter(models.Q(author__is_superuser=True) | models.Q(author=agent_site.user))
            else:
                queryset = queryset.filter(author=agent_site.user)
        return queryset

    def dispatch(self, request, *args, **kwargs):
        agent_site = getattr(request, 'current_agent_site', None)
        if agent_site and not agent_site.show_news:
            if agent_site.slug:
                return redirect('agent_home', slug=agent_site.slug)
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


# -------------------------
# Детальна сторінка новини
# -------------------------
def news_detail(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    agent_site = getattr(request, 'current_agent_site', None)

    if agent_site and not agent_site.show_news:
        if agent_site.slug:
            return redirect('agent_home', slug=agent_site.slug)
        return redirect('home')

    recommended = News.objects.exclude(pk=pk).order_by('?')[:3] if not (agent_site and not agent_site.show_news) else []

    if request.method == 'POST' and 'consultation_submit' in request.POST:
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        if name and phone:
            agent = agent_site.user if agent_site else None
            Consultation.objects.create(
                name=name,
                phone=phone,
                comment=f"Заявка з новини «{news_item.title}»",
                agent=agent
            )
            messages.success(request, 'Ваш запит прийнято. Ми звʼяжемося з вами найближчим часом.')
            referer = request.META.get('HTTP_REFERER', '/')
            return redirect(referer)

    colors = get_agent_colors(request)

    context = {
        'news_item': news_item,
        'random_agent': get_random_agent(),
        'recommended': recommended,
        'agent_site': agent_site,
    }
    context.update(colors)

    return render(request, 'tours/news_detail.html', context)


# -------------------------
# LIVE SEARCH
# -------------------------
def live_search(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)

    agent_site = getattr(request, 'current_agent_site', None)

    tours = Tour.objects.all()

    if agent_site:
        if agent_site.show_superadmin_tours:
            tours = tours.filter(models.Q(author__is_superuser=True) | models.Q(author=agent_site.user))
        else:
            tours = tours.filter(author=agent_site.user)

    matching_tours = []
    query_lower = query.lower()
    for tour in tours:
        if (query_lower in tour.title.lower() or
                query_lower in tour.country.lower() or
                (tour.description and query_lower in tour.description.lower())):
            matching_tours.append(tour)
            if len(matching_tours) >= 10:
                break

    data = [{"id": t.id, "title": t.title, "country": t.country, "price": str(t.price)} for t in matching_tours]
    return JsonResponse(data, safe=False)


# -------------------------
# Сторінка результатів пошуку
# -------------------------
def search_results(request):
    agent_site = getattr(request, 'current_agent_site', None)

    tours = Tour.objects.all()
    tours = filter_tours_by_agent_site(tours, request)

    country = request.GET.get('country')
    if country:
        tours = tours.filter(country__icontains=country)

    cities = request.GET.getlist('cities')
    cities = [c for c in cities if c.strip() != '']
    if cities:
        tours = tours.filter(city__name__in=cities)

    hotel = request.GET.get('hotel')
    if hotel:
        tours = tours.filter(title__icontains=hotel)

    departure_city = request.GET.get('departure_city')
    if departure_city:
        tours = tours.filter(departure_city__icontains=departure_city)

    start_date_iso = request.GET.get('start_date_iso')
    end_date_iso = request.GET.get('end_date_iso')
    if start_date_iso and end_date_iso:
        tours = tours.filter(start_date__gte=start_date_iso, start_date__lte=end_date_iso)

    nights_min = request.GET.get('nights_min')
    nights_max = request.GET.get('nights_max')
    if nights_min and nights_max:
        tours = tours.filter(duration__gte=nights_min, duration__lte=nights_max)

    rating_values = request.GET.getlist('rating')
    for r in rating_values:
        if r == '1':
            tours = tours.filter(reviews__rating__gte=1, reviews__rating__lt=2)
        elif r == '1.5':
            tours = tours.filter(reviews__rating__gte=1.5, reviews__rating__lt=2.5)
        elif r == '2':
            tours = tours.filter(reviews__rating__gte=2, reviews__rating__lt=3)
        elif r == '2.5':
            tours = tours.filter(reviews__rating__gte=2.5, reviews__rating__lt=3.5)
        elif r == '3':
            tours = tours.filter(reviews__rating__gte=3, reviews__rating__lt=4)
        elif r == '3.5':
            tours = tours.filter(reviews__rating__gte=3.5, reviews__rating__lt=4.5)
        elif r == '4':
            tours = tours.filter(reviews__rating__gte=4, reviews__rating__lt=5)
        elif r == '4.5':
            tours = tours.filter(reviews__rating__gte=4.5, reviews__rating__lt=5.5)
        elif r == '5':
            tours = tours.filter(reviews__rating=5)

    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        tours = tours.filter(price__gte=Decimal(price_min))
    if price_max:
        tours = tours.filter(price__lte=Decimal(price_max))

    stars = request.GET.getlist('stars')
    if stars:
        tours = tours.filter(stars__in=stars)

    hotel_search = request.GET.get('hotel_search')
    if hotel_search:
        tours = tours.filter(title__icontains=hotel_search)

    meal_ids = request.GET.getlist('meal')
    if meal_ids:
        tours = tours.filter(amenities__id__in=meal_ids).distinct()

    beach_ids = request.GET.getlist('beach_line')
    if beach_ids:
        tours = tours.filter(amenities__id__in=beach_ids).distinct()

    if request.GET.get('adults_only'):
        tours = tours.filter(amenities__name__name__icontains='Готель для дорослих')
    if request.GET.get('large_area'):
        tours = tours.filter(amenities__name__name__icontains='Велика територія')
    if request.GET.get('waterpark'):
        tours = tours.filter(amenities__name__name__icontains='Аквапарк або гірки')

    adults = int(request.GET.get('adults', 2))
    children_data = request.GET.get('children_data', '[]')
    try:
        children_ages = json.loads(children_data)
    except:
        children_ages = []

    infants = sum(1 for age in children_ages if age == 0)
    children_2_3 = sum(1 for age in children_ages if 2 <= age <= 3)
    children_4_10 = sum(1 for age in children_ages if 4 <= age <= 10)
    children_11_16 = sum(1 for age in children_ages if 11 <= age <= 16)

    price_subquery = TourPriceByTourists.objects.filter(
        tour=OuterRef('pk'),
        adults=adults,
        infants=infants,
        children_2_3=children_2_3,
        children_4_10=children_4_10,
        children_11_16=children_11_16
    ).values('price')[:1]

    default_price_subquery = TourPriceByTourists.objects.filter(
        tour=OuterRef('pk'),
        is_default=True
    ).values('price')[:1]

    tours = tours.annotate(
        custom_price=Subquery(price_subquery),
        default_custom_price=Subquery(default_price_subquery),
        effective_price=Case(
            When(custom_price__isnull=False, then=F('custom_price')),
            When(default_custom_price__isnull=False, then=F('default_custom_price')),
            default=F('price'),
            output_field=models.DecimalField()
        )
    )

    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        tours = tours.order_by('effective_price')
    elif sort_by == 'price_desc':
        tours = tours.order_by('-effective_price')
    elif sort_by == 'rating_desc':
        tours = tours.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        tours = tours.order_by('-created_at')

    tours = tours.annotate(
        avg_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews'),
        earliest_departure=Min('start_date'),
        typical_nights=Avg(ExpressionWrapper(F('end_date') - F('start_date'), output_field=DurationField()))
    )

    popular_tours_for_country = []
    if country:
        popular_qs = Tour.objects.filter(country=country, is_popular=True).annotate(
            avg_rating=Avg('reviews__rating'),
            reviews_count=Count('reviews')
        )
        popular_qs = filter_tours_by_agent_site(popular_qs, request)
        popular_tours_for_country = popular_qs.order_by('?')[:6]

    country_info = None
    if country:
        try:
            country_info = CountryInfo.objects.get(country__iexact=country)
        except CountryInfo.DoesNotExist:
            pass

    similar_cities = []
    if country:
        tours_for_country = filter_tours_by_agent_site(Tour.objects.filter(country=country), request)
        similar_cities = City.objects.filter(
            country=country,
            tour__in=tours_for_country
        ).annotate(
            tours_count=Count('tour')
        ).order_by('-tours_count')[:8]
        for city in similar_cities:
            first_tour = tours_for_country.filter(city=city).first()
            city.image_url = first_tour.image.url if first_tour and first_tour.image else ''

    paginator = Paginator(tours, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    meal_options = Amenity.objects.filter(name__name__icontains='харчування')
    beach_lines = Amenity.objects.filter(name__name__icontains='лінія')

    colors = get_agent_colors(request)

    context = {
        'tours': page_obj,
        'meal_options': meal_options,
        'beach_lines': beach_lines,
        'request': request,
        'adults': adults,
        'children_ages': children_ages,
        'popular_tours_for_country': popular_tours_for_country,
        'country_info': country_info,
        'similar_cities': similar_cities,
        'random_agent': get_random_agent(),
        'agent_site': agent_site,
    }
    context.update(colors)

    return render(request, 'tours/search_results.html', context)


# -------------------------
# AJAX для отримання курортів
# -------------------------
def get_cities(request):
    country = request.GET.get('country')
    if country:
        tours_for_country = filter_tours_by_agent_site(Tour.objects.filter(country__icontains=country), request)
        cities = City.objects.filter(
            country__icontains=country,
            tour__in=tours_for_country
        ).values_list('name', flat=True).distinct().order_by('name')
        return JsonResponse(list(cities), safe=False)
    return JsonResponse([], safe=False)


# -------------------------
# Консультація
# -------------------------
class ConsultationCreateView(CreateView):
    model = Consultation
    form_class = ConsultationForm
    template_name = 'tours/consultation_form.html'
    success_url = None

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        agent_site = getattr(self.request, 'current_agent_site', None)
        form.instance.agent = agent_site.user if agent_site else None
        self.object = form.save()
        messages.success(self.request, 'Дякуємо за відгук! Ми відповімо вам найближчим часом.')

        next_url = self.request.POST.get('next')
        if next_url:
            return redirect(next_url)
        if agent_site:
            return redirect('agent_home', slug=agent_site.slug)
        return redirect('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Допомогти обрати тур'
        return context


class ConsultationSuccessView(TemplateView):
    template_name = 'tours/consultation_success.html'


# -------------------------
# Політика конфіденційності та правила надання послуг
# -------------------------
def privacy_policy(request):
    return render(request, 'tours/privacy_policy.html')


def terms_of_service(request):
    return render(request, 'tours/terms_of_service.html')


# -------------------------
# API для календаря низьких цін
# -------------------------
def calendar_prices(request):
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

    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    tours = Tour.objects.filter(
        country__icontains=country,
        start_date__gte=start_date,
        start_date__lt=end_date
    )

    if departure:
        tours = tours.filter(departure_city__icontains=departure)

    if slug:
        try:
            from constructor.models import AgentSite
            agent_site = AgentSite.objects.select_related('user').get(slug=slug)
            if agent_site.show_superadmin_tours:
                tours = tours.filter(models.Q(author__is_superuser=True) | models.Q(author=agent_site.user))
            else:
                tours = tours.filter(author=agent_site.user)
        except AgentSite.DoesNotExist:
            pass
    else:
        tours = filter_tours_by_agent_site(tours, request)

    price_by_day = {}
    for tour in tours:
        day = tour.start_date.day
        if day not in price_by_day or tour.price < price_by_day[day]:
            price_by_day[day] = tour.price

    days_in_month = (end_date - start_date).days
    prices = []
    for day in range(1, days_in_month + 1):
        prices.append(price_by_day.get(day, None))

    max_price = max([p for p in prices if p is not None], default=50000)

    return JsonResponse({'prices': prices, 'max_price': max_price})


# -------------------------
# API для отримання ціни залежно від складу туристів
# -------------------------
@csrf_exempt
def get_price_options(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    departure_date = request.GET.get('departure_date')
    duration = request.GET.get('duration')
    adults = int(request.GET.get('adults', 2))
    infants = int(request.GET.get('infants', 0))
    children_2_3 = int(request.GET.get('children_2_3', 0))
    children_4_10 = int(request.GET.get('children_4_10', 0))
    children_11_16 = int(request.GET.get('children_11_16', 0))

    price_option = PriceOption.objects.filter(
        tour=tour,
        departure_date=departure_date,
        duration=duration,
        adults=adults,
        infants=infants,
        children_2_3=children_2_3,
        children_4_10=children_4_10,
        children_11_16=children_11_16,
        is_available=True
    ).first()

    if price_option:
        return JsonResponse({'price': str(price_option.price), 'found': True})
    return JsonResponse({'found': False, 'message': 'Ціна для вибраного складу не знайдена'})


# -------------------------
# AJAX для блоку "Тури з вашого міста"
# -------------------------
def tours_by_city(request):
    city = request.GET.get('city')
    if not city:
        return JsonResponse({'error': 'City required'}, status=400)

    agent_site = getattr(request, 'current_agent_site', None)

    tours = Tour.objects.filter(departure_city=city).annotate(
        avg_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews')
    )

    if agent_site:
        if agent_site.show_superadmin_tours:
            tours = tours.filter(models.Q(author__is_superuser=True) | models.Q(author=agent_site.user))
        else:
            tours = tours.filter(author=agent_site.user)
    else:
        tours = tours

    countries_dict = {}
    for tour in tours:
        if not tour.country or not tour.price or not tour.start_date:
            continue

        country = tour.country
        if country not in countries_dict:
            countries_dict[country] = {
                'country': country,
                'image_url': tour.image.url if tour.image else '',
                'min_price': tour.price,
                'closest_date': tour.start_date,
                'avg_rating': tour.avg_rating,
            }
        else:
            if tour.price < countries_dict[country]['min_price']:
                countries_dict[country]['min_price'] = tour.price
            if tour.start_date < countries_dict[country]['closest_date']:
                countries_dict[country]['closest_date'] = tour.start_date

    data = []
    for country, info in countries_dict.items():
        if info['min_price'] is not None and info['closest_date'] is not None:
            data.append({
                'country': info['country'],
                'image_url': info['image_url'],
                'min_price': float(info['min_price']) if info['min_price'] else None,
                'closest_date': info['closest_date'].strftime('%d.%m') if info['closest_date'] else None,
                'avg_rating': float(info['avg_rating']) if info['avg_rating'] else None,
            })

    return JsonResponse({'countries': data})


# -------------------------
# Детальна сторінка міста (курорту)
# -------------------------
def city_detail(request, city_id):
    city = get_object_or_404(City, pk=city_id)
    agent_site = getattr(request, 'current_agent_site', None)

    tours = Tour.objects.filter(city=city).annotate(
        avg_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews')
    )

    tours = filter_tours_by_agent_site(tours, request)

    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        tours = tours.order_by('price')
    elif sort_by == 'price_desc':
        tours = tours.order_by('-price')
    elif sort_by == 'rating_desc':
        tours = tours.order_by('-avg_rating')
    else:
        tours = tours.order_by('-created_at')

    paginator = Paginator(tours, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    tours_for_country = filter_tours_by_agent_site(Tour.objects.filter(country=city.country), request)
    similar_cities = City.objects.filter(
        country=city.country,
        tour__in=tours_for_country
    ).exclude(pk=city.pk).annotate(
        tours_count=Count('tour')
    ).order_by('-tours_count')[:6]

    for similar in similar_cities:
        first_tour = tours_for_country.filter(city=similar).first()
        similar.image_url = first_tour.image.url if first_tour and first_tour.image else ''

    colors = get_agent_colors(request)

    context = {
        'city': city,
        'tours': page_obj,
        'sort_by': sort_by,
        'similar_cities': similar_cities,
        'random_agent': get_random_agent(),
        'agent_site': agent_site,
    }
    context.update(colors)

    return render(request, 'tours/city_detail.html', context)


# -------------------------
# API для чату (ШІ-асистент)
# -------------------------
def chat_api(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        message = data.get('message', '')

        if not message:
            return JsonResponse({'error': 'Повідомлення не може бути пустим'}, status=400)

        agent_site = getattr(request, 'current_agent_site', None)
        agency_name = agent_site.agency_name if agent_site and agent_site.agency_name else "Моя Агенція"

        result = get_gemini_response(message, request, agency_name)

        response_data = {'response': result['text']}

        if result.get('redirect'):
            redirect_url = result['redirect']
            if agent_site and redirect_url.startswith('/search/'):
                redirect_url = f'/a/{agent_site.slug}/search/' + redirect_url.replace('/search/', '?')
            elif agent_site and redirect_url.startswith('/tour/'):
                redirect_url = f'/a/{agent_site.slug}' + redirect_url
            elif agent_site and redirect_url.startswith('/city/'):
                redirect_url = f'/a/{agent_site.slug}' + redirect_url
            response_data['redirect'] = redirect_url

        if result.get('consultation_link'):
            consultation_link = result['consultation_link']
            if agent_site and consultation_link.startswith('/consultation/'):
                consultation_link = f'/a/{agent_site.slug}/consultation/'
            response_data['consultation_link'] = consultation_link

        return JsonResponse(response_data)

    return JsonResponse({'error': 'Method not allowed'}, status=405)