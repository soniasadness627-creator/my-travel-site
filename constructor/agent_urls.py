from django.urls import path
from . import views

urlpatterns = [
    # Головна сторінка агента
    path('', views.agent_public_site, name='agent_home'),

    # Деталі туру
    path('tour/<int:pk>/', views.agent_public_site, name='agent_tour_detail'),

    # Відгуки про тур
    path('tour/<int:pk>/reviews/', views.agent_public_site, name='agent_tour_reviews'),

    # Пошук
    path('search/', views.agent_public_site, name='agent_search'),

    # Новини
    path('news/', views.agent_public_site, name='agent_news'),
    path('news/<int:pk>/', views.agent_public_site, name='agent_news_detail'),

    # Місто
    path('city/<int:city_id>/', views.agent_public_site, name='agent_city_detail'),

    # Консультація
    path('consultation/', views.agent_public_site, name='agent_consultation'),

    # Політика конфіденційності
    path('privacy-policy/', views.agent_public_site, name='agent_privacy_policy'),

    # Правила надання послуг
    path('terms-of-service/', views.agent_public_site, name='agent_terms_of_service'),

    # Вхід для агента
    path('login/', views.agent_login, name='agent_login'),

    # ========== API ДЛЯ ВІДГУКІВ (ДЛЯ АГЕНТСЬКИХ САЙТІВ) ==========
    path('api/hotel-reviews/', views.hotel_reviews_api, name='agent_hotel_reviews_api'),
]