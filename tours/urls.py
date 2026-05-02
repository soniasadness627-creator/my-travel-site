from django.urls import path
from . import views

urlpatterns = [
    # Головна сторінка з пошуком
    path('', views.home, name='home'),

    # API для календаря низьких цін
    path('api/calendar-prices/', views.calendar_prices_otpusk, name='calendar_prices'),

    # API для чату
    path('api/chat/', views.chat_api, name='chat_api'),

    # Сторінка результатів пошуку Otpusk
    path('search-otpusk/', views.search_otpusk, name='search_otpusk'),

    # Консультація
    path('consultation/', views.ConsultationCreateView.as_view(), name='consultation'),

    # AJAX для отримання міст
    path('get-cities/', views.get_cities, name='get_cities'),

    # Вихід
    path('logout/', views.custom_logout, name='logout'),
]