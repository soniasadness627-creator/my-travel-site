from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import custom_logout

urlpatterns = [
    # Головна сторінка (список турів)
    path('', views.TourListView.as_view(), name='home'),

    # Пошук
    path('search/', views.search_results, name='search_results'),
    path('get-cities/', views.get_cities, name='get_cities'),
    path('api/calendar-prices/', views.calendar_prices, name='calendar_prices'),

    # Деталі туру
    path('tour/<int:pk>/', views.tour_detail, name='tour_detail'),
    path('tour/<int:pk>/reviews/', views.tour_reviews, name='tour_reviews'),

    # Дашборд агента
    path('dashboard/', views.AgentDashboardView.as_view(), name='dashboard'),

    # CRUD турів
    path('tour/new/', views.TourCreateView.as_view(), name='tour_create'),
    path('tour/<int:pk>/edit/', views.TourUpdateView.as_view(), name='tour_edit'),
    path('tour/<int:pk>/delete/', views.TourDeleteView.as_view(), name='tour_delete'),

    # Живий пошук
    path('live-search/', views.live_search, name='live_search'),

    # Новини
    path('news/', views.NewsListView.as_view(), name='news'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),

    # Консультація
    path('consultation/', views.ConsultationCreateView.as_view(), name='consultation'),
    path('consultation/success/', views.ConsultationSuccessView.as_view(), name='consultation_success'),

    # Політика та правила
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),

    # Вихід
    path('logout/', custom_logout, name='logout'),

    # AJAX для блоку "Тури з вашого міста"
    path('tours-by-city/', views.tours_by_city, name='tours_by_city'),

    # Детальна сторінка міста
    path('city/<int:city_id>/', views.city_detail, name='city_detail'),

    # API для отримання ціни
    path('api/price-options/<int:tour_id>/', views.get_price_options, name='get_price_options'),

    # ========== НОВИЙ МАРШРУТ ДЛЯ ЧАТУ ==========
    path('api/chat/', views.chat_api, name='chat_api'),
]