from django.urls import path
from . import views

urlpatterns = [
    # Головна сторінка з пошуком
    path('', views.home, name='home'),

    # API для календаря низьких цін
    path('api/calendar-prices/', views.calendar_prices_otpusk, name='calendar_prices'),

    # API для чату
    path('api/chat/', views.chat_api, name='chat_api'),

    # ========== API ДЛЯ ВІДГУКІВ ==========
    path('api/hotel-reviews/', views.hotel_reviews_api, name='hotel_reviews_api'),

    # Сторінка результатів пошуку Otpusk
    path('search-otpusk/', views.search_otpusk, name='search_otpusk'),

    # Сторінка результатів пошуку для популярних напрямків
    path('search-otpusk-by-country/', views.search_otpusk_by_country, name='search_otpusk_by_country'),

    # Деталі туру
    path('tour-detail/', views.tour_detail_otpusk, name='tour_detail_otpusk'),

    # Консультація
    path('consultation/', views.ConsultationCreateView.as_view(), name='consultation'),

    # AJAX для отримання міст
    path('get-cities/', views.get_cities, name='get_cities'),

    # AJAX для консультації
    path('consultation-ajax/', views.consultation_ajax, name='consultation_ajax'),

    # Вихід
    path('logout/', views.custom_logout, name='logout'),
]