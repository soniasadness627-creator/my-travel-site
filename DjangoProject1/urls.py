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


# ========== ФУНКЦІЯ ДЛЯ ПЕРЕНАПРАВЛЕННЯ ГОЛОВНОЇ СТОРІНКИ ==========
def home_redirect(request):
    """Перенаправляє суперадміна на сторінку турів, інших - на лендинг"""
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/home/')  # сторінка турів для суперадміна
    return redirect('/landing/')  # лендинг для всіх інших


urlpatterns = [
    # ========== ГОЛОВНА СТОРІНКА ==========
    path('', home_redirect, name='home_redirect'),
    path('landing/', include('landing.urls')),  # лендинг доступний за /landing/

    # ========== АДМІН-ПАНЕЛІ ==========
    path('admin/', admin.site.urls, name='admin'),
    path('a/<slug:slug>/admin/', agent_admin_site.urls),  # Агентська адмінка

    path('chaining/', include('smart_selects.urls')),

    # ========== ОСНОВНІ МАРШРУТИ ТУРІВ ==========
    path('home/', tours_views.TourListView.as_view(), name='home'),
    path('search/', tours_views.search_results, name='search_results'),
    path('get-cities/', tours_views.get_cities, name='get_cities'),
    path('api/calendar-prices/', tours_views.calendar_prices, name='calendar_prices'),
    path('tour/<int:pk>//', tours_views.tour_detail, name='tour_detail'),
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
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)