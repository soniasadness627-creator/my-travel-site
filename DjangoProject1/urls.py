from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from tours import views as tours_views
from constructor import views as constructor_views
from constructor.agent_admin import agent_admin_site
from landing import views as landing_views
from django.views.generic import TemplateView
from tours.admin import mass_email_admin

# ========== ОБРОБНИК ПОМИЛКИ CSRF ==========
from django.views.csrf import csrf_failure


# ========== ФУНКЦІЯ ДЛЯ ПЕРЕНАПРАВЛЕННЯ ГОЛОВНОЇ СТОРІНКИ ==========
def home_redirect(request):
    """
    Перенаправляє:
    - Локально (127.0.0.1 або localhost) завжди на лендинг
    - На Render: суперадміна на /home/, інших на /landing/
    """
    host = request.META.get('HTTP_HOST', '')

    if host.startswith('127.0.0.1') or host.startswith('localhost'):
        return redirect('/landing/')

    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/home/')
    return redirect('/landing/')


def custom_csrf_failure(request, reason=""):
    return redirect('/')


handler403 = custom_csrf_failure

urlpatterns = [
    # ========== МАСОВА EMAIL-РОЗСИЛКА ==========
    path('admin/mass-email/', mass_email_admin.urls, name='mass_email'),

    # ========== МАРШРУТ ДЛЯ СТВОРЕННЯ СУПЕРАДМІНА ==========
    path('create-admin/', constructor_views.create_admin_direct, name='create_admin'),

    # ========== ГОЛОВНА СТОРІНКА ==========
    path('', home_redirect, name='home_redirect'),
    path('landing/', include('landing.urls')),

    # ========== АДМІН-ПАНЕЛІ ==========
    path('admin/', admin.site.urls, name='admin'),
    path('a/admin/', agent_admin_site.urls, name='agent_admin'),

    path('chaining/', include('smart_selects.urls')),

    # ========== ОСНОВНІ МАРШРУТИ ==========
    path('home/', tours_views.home, name='home'),
    path('news/', tours_views.NewsListView.as_view(), name='news'),
    path('news/<int:pk>/', tours_views.news_detail, name='news_detail'),

    # ========== API КАЛЕНДАРЯ ЦІН ==========
    path('api/calendar-prices/', tours_views.calendar_prices_otpusk, name='calendar_prices'),
    path('api/calendar-prices-cached/', tours_views.calendar_prices_cached, name='calendar_prices_cached'),

    # ========== ІНШІ API ==========
    path('get-cities/', tours_views.get_cities, name='get_cities'),
    path('api/chat/', tours_views.chat_api, name='chat_api'),
    path('api/popular-tours/', tours_views.popular_tours_api, name='popular_tours_api'),
    path('api/get-popular-tours/', tours_views.get_popular_tours_api, name='get_popular_tours'),
    path('api/get-popular-hotels/', tours_views.get_popular_hotels_api, name='get_popular_hotels'),

    # ========== API ДЛЯ ВІДГУКІВ ==========
    path('api/hotel-reviews/', tours_views.hotel_reviews_api, name='hotel_reviews_api'),
    path('a/<slug:slug>/api/hotel-reviews/', tours_views.hotel_reviews_api, name='agent_hotel_reviews_api'),

    # ========== AJAX ОБРОБКА ==========
    path('consultation-ajax/', tours_views.consultation_ajax, name='consultation_ajax'),
    path('a/<slug:slug>/consultation-ajax/', tours_views.consultation_ajax, name='agent_consultation_ajax'),
    path('booking-ajax/', tours_views.booking_ajax, name='booking_ajax'),
    path('a/<slug:slug>/booking-ajax/', tours_views.booking_ajax, name='agent_booking_ajax'),

    # ========== СТОРІНКИ ПОШУКУ ==========
    path('search-otpusk/', tours_views.search_otpusk, name='search_otpusk'),
    path('a/<slug:slug>/search-otpusk/', tours_views.search_otpusk, name='agent_search_otpusk'),
    path('search-results-calendar/', tours_views.search_results_calendar, name='search_results_calendar'),
    path('a/<slug:slug>/search-results-calendar/', tours_views.search_results_calendar,
         name='agent_search_results_calendar'),
    path('search-otpusk-by-country/', tours_views.search_otpusk_by_country, name='search_otpusk_by_country'),
    path('a/<slug:slug>/search-otpusk-by-country/', tours_views.search_otpusk_by_country,
         name='agent_search_otpusk_by_country'),
    path('search-otpusk-new/', tours_views.search_otpusk_new, name='search_otpusk_new'),
    path('a/<slug:slug>/search-otpusk-new/', tours_views.search_otpusk_new, name='agent_search_otpusk_new'),

    # ========== ДЕТАЛІ ТУРУ ==========
    path('tour-detail/', tours_views.tour_detail, name='tour_detail'),
    path('a/<slug:slug>/tour-detail/', tours_views.tour_detail, name='agent_tour_detail'),

    # ========== КОНСУЛЬТАЦІЯ ==========
    path('consultation/', TemplateView.as_view(template_name='tours/consultation_form.html'), name='consultation'),

    # ========== АВТЕНТИФІКАЦІЯ ==========
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # ========== ІНШІ СТОРІНКИ ==========
    path('privacy-policy/', landing_views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', landing_views.terms_of_service, name='terms_of_service'),
    path('tours-by-city/', tours_views.tours_by_city, name='tours_by_city'),
    path('city/<int:city_id>/', tours_views.city_detail, name='city_detail'),

    # ========== КОНСТРУКТОР (ВСІ МАРШРУТИ ЧЕРЕЗ INCLUDE) ==========
    path('constructor/', include('constructor.urls')),

    # ========== АГЕНТСЬКІ САЙТИ (ТІЛЬКИ ОСНОВНІ МАРШРУТИ) ==========
    # Всі інші маршрути агента (news/, tour/, consultation/ тощо)
    # обробляються через agent_public_site в views.py
    path('a/<slug:slug>/', constructor_views.agent_public_site, name='agent_home'),
    path('a/<slug:slug>/login/', constructor_views.agent_login, name='agent_login'),

    # ========== АГЕНТСЬКІ API ==========
    path('a/<slug:slug>/api/get-popular-tours/', tours_views.get_popular_tours_api, name='agent_get_popular_tours'),
    path('a/<slug:slug>/api/get-popular-hotels/', tours_views.get_popular_hotels_api, name='agent_get_popular_hotels'),
    path('a/<slug:slug>/api/booking/', constructor_views.booking_api, name='agent_booking_api_direct'),
]

# ========== СТАТИЧНІ ТА МЕДІА ФАЙЛИ ==========
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)