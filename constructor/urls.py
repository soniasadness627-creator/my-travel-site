from django.urls import path, include
from django.views.generic import TemplateView  # ← ДОДАНО ДЛЯ TemplateView
from . import views

app_name = 'constructor'

urlpatterns = [
    path('register/', views.agent_register_step1, name='register'),
    path('verify/', views.agent_verify, name='verify'),
    path('dashboard/', views.constructor_dashboard, name='dashboard'),
    path('open-site/', views.open_site, name='open_site'),
    path('generate-image/', views.generate_image, name='generate_image'),
    path('agent-login-redirect/', views.agent_login_redirect, name='agent_login_redirect'),

    # ========== НОВІ URL ДЛЯ НАЛАШТУВАНЬ БЛОКІВ ==========
    path('blocks-settings/', views.blocks_settings, name='blocks_settings'),
    path('banner/create/', views.banner_create, name='banner_create'),
    path('banner/get/<int:banner_id>/', views.banner_get, name='banner_get'),
    path('banner/delete/<int:banner_id>/', views.banner_delete, name='banner_delete'),
    path('banner/reorder/', views.banner_reorder, name='banner_reorder'),
]

# окремий конфіг для агентських сайтів
agent_urlpatterns = [
    # Сторінка результатів пошуку Otpusk - використовуємо TemplateView напряму (без логіки)
    path('search-otpusk/', TemplateView.as_view(template_name='tours/search_results_otpusk.html'),
         name='agent_search_otpusk'),

    # Основні маршрути агента - використовують agent_public_site
    path('', views.agent_public_site, name='agent_home'),
    path('tour/<int:pk>/', views.agent_public_site, name='agent_tour_detail'),
    path('tour/<int:pk>/reviews/', views.agent_public_site, name='agent_tour_reviews'),
    path('search/', views.agent_public_site, name='agent_search'),
    path('news/', views.agent_public_site, name='agent_news'),
    path('news/<int:pk>/', views.agent_public_site, name='agent_news_detail'),
    path('city/<int:city_id>/', views.agent_public_site, name='agent_city_detail'),
    path('consultation/', views.agent_public_site, name='agent_consultation'),
    path('privacy-policy/', views.agent_public_site, name='agent_privacy_policy'),
    path('terms-of-service/', views.agent_public_site, name='agent_terms_of_service'),
    path('login/', views.agent_login, name='agent_login'),
]