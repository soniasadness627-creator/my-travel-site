from django.urls import path, include
from django.views.generic import TemplateView
from . import views

app_name = 'constructor'

urlpatterns = [
    # ========== РЕЄСТРАЦІЯ ТА ВЕРИФІКАЦІЯ ==========
    path('register/', views.agent_register_step1, name='register'),
    path('verify/', views.agent_verify, name='verify'),

    # ========== ОСНОВНІ МАРШРУТИ КОНСТРУКТОРА ==========
    path('dashboard/', views.constructor_dashboard, name='dashboard'),
    path('open-site/', views.open_site, name='open_site'),
    path('generate-image/', views.generate_image, name='generate_image'),
    path('agent-login-redirect/', views.agent_login_redirect, name='agent_login_redirect'),

    # ========== НАЛАШТУВАННЯ БЛОКІВ ТА БАНЕРІВ ==========
    path('blocks-settings/', views.blocks_settings, name='blocks_settings'),
    path('banner/create/', views.banner_create, name='banner_create'),
    path('banner/get/<int:banner_id>/', views.banner_get, name='banner_get'),
    path('banner/delete/<int:banner_id>/', views.banner_delete, name='banner_delete'),
    path('banner/reorder/', views.banner_reorder, name='banner_reorder'),

    # ========== API ДЛЯ БРОНЮВАННЯ ТУРІВ ==========
    path('api/booking/', views.booking_api, name='booking_api'),

    # ========== AJAX ДЛЯ ЗБЕРЕЖЕННЯ ЗАГОЛОВКІВ ==========
    path('save-hero-ajax/', views.save_hero_ajax, name='save_hero_ajax'),
]

# ============================================================
# МАРШРУТИ ДЛЯ АГЕНТСЬКИХ САЙТІВ (через /a/<slug>/...)
# Ці маршрути підключаються в основному urls.py
# ============================================================
agent_urlpatterns = [
    # ========== API ДЛЯ БРОНЮВАННЯ (ПОВИНЕН БУТИ ПЕРШИМ) ==========
    path('api/booking/', views.booking_api, name='agent_booking_api'),

    # ========== АВТЕНТИФІКАЦІЯ ==========
    path('login/', views.agent_login, name='agent_login'),

    # ========== СТОРІНКИ САЙТУ АГЕНТА ==========
    path('', views.agent_public_site, name='agent_home'),
    path('home/', views.agent_public_site, name='agent_home_redirect'),
    path('news/', views.agent_public_site, name='agent_news_list'),
    path('news/<int:pk>/', views.agent_public_site, name='agent_news_detail'),
    path('tour/<int:pk>/', views.agent_public_site, name='agent_tour_detail'),
    path('tour/<int:pk>/reviews/', views.agent_public_site, name='agent_tour_reviews'),
    path('search/', views.agent_public_site, name='agent_search'),
    path('search-otpusk/', TemplateView.as_view(template_name='tours/search_results_otpusk.html'),
         name='agent_search_otpusk'),
    path('city/<int:city_id>/', views.agent_public_site, name='agent_city_detail'),
    path('consultation/', views.agent_public_site, name='agent_consultation'),
    path('privacy-policy/', views.agent_public_site, name='agent_privacy_policy'),
    path('terms-of-service/', views.agent_public_site, name='agent_terms_of_service'),
]

# ========== ДЛЯ СУМІСНОСТІ ЗІ СТАРИМИ ПОСИЛАННЯМИ ==========
# Якщо є посилання на /a/<slug>/a/admin/ - перенаправляємо
agent_urlpatterns += [
    path('a/admin/', views.agent_public_site, name='agent_admin_redirect'),
]