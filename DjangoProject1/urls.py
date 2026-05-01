from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.views.generic import TemplateView
from tours import views as tours_views
from constructor import views as constructor_views
from constructor.agent_admin import agent_admin_site
from landing import views as landing_views

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
        # Локально завжди показуємо лендинг
        return redirect('/landing/')

    # На Render (продакшен)
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/home/')  # сторінка турів для суперадміна
    return redirect('/landing/')  # лендинг для всіх інших


# ========== ОБРОБНИК ДЛЯ 403 ПОМИЛКИ ==========
def custom_csrf_failure(request, reason=""):
    return redirect('/')

handler403 = custom_csrf_failure

urlpatterns = [
    # ========== МАРШРУТ ДЛЯ СТВОРЕННЯ СУПЕРАДМІНА ==========
    path('create-admin/', constructor_views.create_admin_direct, name='create_admin'),

    # ========== ІНСТРУКЦІЯ ДЛЯ АГЕНТА (чиста сторінка без меню) ==========
    path('instruction/', TemplateView.as_view(template_name='pages/instruction_clean.html'), name='instruction'),

    # ========== ТЕСТОВА СТОРІНКА ДЛЯ ПОШУКУ ТУРІВ ==========
    path('search-test/', TemplateView.as_view(template_name='pages/test_search.html'), name='test_search'),

    # ========== СТОРІНКА РЕЗУЛЬТАТІВ ПОШУКУ OTPUSK (ОКРЕМА СТОРІНКА) ==========
    path('search-otpusk/', TemplateView.as_view(template_name='tours/search_results_otpusk.html'), name='search_otpusk'),
    path('a/<slug:slug>/search-otpusk/', TemplateView.as_view(template_name='tours/search_results_otpusk.html'), name='agent_search_otpusk'),

    # ========== СТОРІНКА РЕЗУЛЬТАТІВ ПОШУКУ (для модуля Otpusk) ==========
    path('search-results/', TemplateView.as_view(template_name='pages/test_search.html'), name='search_results'),

    # ========== ГОЛОВНА СТОРІНКА ==========
    path('', home_redirect, name='home_redirect'),
    path('landing/', include('landing.urls')),  # лендинг доступний за /landing/

    # ========== АДМІН-ПАНЕЛІ ==========
    path('admin/', admin.site.urls, name='admin'),
    path('a/admin/', agent_admin_site.urls, name='agent_admin'),

    path('chaining/', include('smart_selects.urls')),

    # ========== ОСНОВНІ МАРШРУТИ ТУРІВ ==========
    path('home/', tours_views.TourListView.as_view(), name='home'),
    path('search/', tours_views.search_results, name='search_results'),
    path('get-cities/', tours_views.get_cities, name='get_cities'),
    path('api/calendar-prices/', tours_views.calendar_prices, name='calendar_prices'),
    path('tour/<int:pk>/', tours_views.tour_detail, name='tour_detail'),
    path('tour/<int:pk>/reviews/', tours_views.tour_reviews, name='tour_reviews'),

    # ========== КАБІНЕТ АГЕНТА ==========
    path('dashboard/', tours_views.AgentDashboardView.as_view(), name='dashboard'),
    path('tour/new/', tours_views.TourCreateView.as_view(), name='tour_create'),
    path('tour/<int:pk>/edit/', tours_views.TourUpdateView.as_view(), name='tour_edit'),
    path('tour/<int:pk>/delete/', tours_views.TourDeleteView.as_view(), name='tour_delete'),

    # ========== НОВИНИ ==========
    path('live-search/', tours_views.live_search, name='live_search'),
    path('news/', tours_views.NewsListView.as_view(), name='news'),
    path('news/<int:pk>/', tours_views.news_detail, name='news_detail'),

    # ========== КОНСУЛЬТАЦІЯ ==========
    path('consultation/', tours_views.ConsultationCreateView.as_view(), name='consultation'),
    path('consultation/success/', tours_views.ConsultationSuccessView.as_view(), name='consultation_success'),

    # ========== ГЛОБАЛЬНИЙ ВХІД ТА ВИХІД ==========
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # ========== ІНШІ СТОРІНКИ ==========
    path('privacy-policy/', landing_views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', landing_views.terms_of_service, name='terms_of_service'),
    path('tours-by-city/', tours_views.tours_by_city, name='tours_by_city'),
    path('city/<int:city_id>/', tours_views.city_detail, name='city_detail'),
    path('api/price-options/<int:tour_id>/', tours_views.get_price_options, name='get_price_options'),
    path('api/chat/', tours_views.chat_api, name='chat_api'),

    # ========== КОРИСТУВАЧІ ==========
    path('users/', include('users.urls')),

    # ========== КОНСТРУКТОР ==========
    path('constructor/', include('constructor.urls')),

    # ========== АГЕНТСЬКІ САЙТИ ==========
    path('a/<slug:slug>/', constructor_views.agent_public_site, name='agent_home'),
    path('a/<slug:slug>/tour/<int:pk>/', constructor_views.agent_public_site, name='agent_tour_detail'),
    path('a/<slug:slug>/tour/<int:pk>/reviews/', constructor_views.agent_public_site, name='agent_tour_reviews'),
    path('a/<slug:slug>/search/', constructor_views.agent_public_site, name='agent_search'),
    path('a/<slug:slug>/city/<int:city_id>/', constructor_views.agent_public_site, name='agent_city_detail'),
    path('a/<slug:slug>/news/', constructor_views.agent_public_site, name='agent_news_list'),
    path('a/<slug:slug>/news/<int:pk>/', constructor_views.agent_public_site, name='agent_news_detail'),
    path('a/<slug:slug>/consultation/', constructor_views.agent_public_site, name='agent_consultation'),
    path('a/<slug:slug>/privacy-policy/', constructor_views.agent_public_site, name='agent_privacy_policy'),
    path('a/<slug:slug>/terms-of-service/', constructor_views.agent_public_site, name='agent_terms_of_service'),
    path('a/<slug:slug>/login/', constructor_views.agent_public_site, name='agent_login'),
]

# ========== СТАТИЧНІ ТА МЕДІА ФАЙЛИ ==========
# Цей блок відповідає за відображення картинок в продакшені
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # КЛЮЧОВИЙ МОМЕНТ ДЛЯ ПРОДАКШЕНУ - медіа файли мають віддаватися завжди
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)