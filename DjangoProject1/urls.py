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

    # Перевіряємо, чи це локальний запит
    if host.startswith('127.0.0.1') or host.startswith('localhost'):
        return redirect('/landing/')

    # На Render (продакшен)
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/home/')
    return redirect('/landing/')


# ========== ОБРОБНИК ДЛЯ 403 ПОМИЛКИ ==========
def custom_csrf_failure(request, reason=""):
    return redirect('/')


handler403 = custom_csrf_failure

urlpatterns = [
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

    # ========== НОВИЙ МАРШРУТ ДЛЯ КАЛЕНДАРЯ (OTPUSK) ==========
    path('api/calendar-prices/', tours_views.calendar_prices_otpusk, name='calendar_prices'),

    # ========== ІНШІ API МАРШРУТИ ==========
    path('get-cities/', tours_views.get_cities, name='get_cities'),
    path('api/chat/', tours_views.chat_api, name='chat_api'),
    path('api/popular-tours/', tours_views.popular_tours_api, name='popular_tours_api'),

    # ========== AJAX ОБРОБКА КОНСУЛЬТАЦІЇ ==========
    path('consultation-ajax/', tours_views.consultation_ajax, name='consultation_ajax'),
    # ДЛЯ АГЕНТСЬКИХ САЙТІВ
    path('a/<slug:slug>/consultation-ajax/', tours_views.consultation_ajax, name='agent_consultation_ajax'),

    # ========== AJAX ОБРОБКА БРОНЮВАННЯ (BOOKING) ==========
    path('booking-ajax/', tours_views.booking_ajax, name='booking_ajax'),
    # ДЛЯ АГЕНТСЬКИХ САЙТІВ
    path('a/<slug:slug>/booking-ajax/', tours_views.booking_ajax, name='agent_booking_ajax'),

    # ========== СТОРІНКА РЕЗУЛЬТАТІВ ПОШУКУ OTPUSK ==========
    # Сторінка для звичайного пошуку (без блоку консультації)
    path('search-otpusk/', tours_views.search_otpusk, name='search_otpusk'),
    path('a/<slug:slug>/search-otpusk/', tours_views.search_otpusk, name='agent_search_otpusk'),

    # ========== НОВА СТОРІНКА ДЛЯ ПОПУЛЯРНИХ НАПРЯМКІВ (З БЛОКОМ КОНСУЛЬТАЦІЇ) ==========
    path('search-otpusk-by-country/', tours_views.search_otpusk_by_country, name='search_otpusk_by_country'),
    path('a/<slug:slug>/search-otpusk-by-country/', tours_views.search_otpusk_by_country,
         name='agent_search_otpusk_by_country'),

    # ========== НОВА СТОРІНКА ДЛЯ ДЕТАЛЬНОГО ПЕРЕГЛЯДУ ТУРУ (БЕЗ ФОРМИ ПОШУКУ) ==========
    path('tour-detail/', tours_views.tour_detail_otpusk, name='tour_detail_otpusk'),
    path('a/<slug:slug>/tour-detail/', tours_views.tour_detail_otpusk, name='agent_tour_detail_otpusk'),

    # ========== КОНСУЛЬТАЦІЯ (ЗВИЧАЙНА ФОРМА З ПЕРЕНАПРАВЛЕННЯМ) ==========
    path('consultation/', TemplateView.as_view(template_name='tours/consultation_form.html'), name='consultation'),

    # ========== ГЛОБАЛЬНИЙ ВХІД ТА ВИХІД ==========
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # ========== ІНШІ СТОРІНКИ ==========
    path('privacy-policy/', landing_views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', landing_views.terms_of_service, name='terms_of_service'),
    path('tours-by-city/', tours_views.tours_by_city, name='tours_by_city'),
    path('city/<int:city_id>/', tours_views.city_detail, name='city_detail'),

    # ========== КОНСТРУКТОР ==========
    path('constructor/', include('constructor.urls')),

    # ========== АГЕНТСЬКІ САЙТИ ==========
    path('a/<slug:slug>/', constructor_views.agent_public_site, name='agent_home'),
    path('a/<slug:slug>/tour/<int:pk>/', constructor_views.agent_public_site, name='agent_tour_detail'),
    path('a/<slug:slug>/tour/<int:pk>/reviews/', constructor_views.agent_public_site, name='agent_tour_reviews'),
    path('a/<slug:slug>/city/<int:city_id>/', constructor_views.agent_public_site, name='agent_city_detail'),
    path('a/<slug:slug>/news/', constructor_views.agent_public_site, name='agent_news_list'),
    path('a/<slug:slug>/news/<int:pk>/', constructor_views.agent_public_site, name='agent_news_detail'),
    path('a/<slug:slug>/consultation/', constructor_views.agent_public_site, name='agent_consultation'),
    path('a/<slug:slug>/privacy-policy/', constructor_views.agent_public_site, name='agent_privacy_policy'),
    path('a/<slug:slug>/terms-of-service/', constructor_views.agent_public_site, name='agent_terms_of_service'),
    path('a/<slug:slug>/login/', constructor_views.agent_public_site, name='agent_login'),
]

# ========== СТАТИЧНІ ТА МЕДІА ФАЙЛИ ==========
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)