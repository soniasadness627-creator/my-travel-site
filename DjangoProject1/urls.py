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


def home_redirect(request):
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
    path('create-admin/', constructor_views.create_admin_direct, name='create_admin'),

    path('', home_redirect, name='home_redirect'),
    path('landing/', include('landing.urls')),

    path('admin/', admin.site.urls, name='admin'),
    path('a/admin/', agent_admin_site.urls, name='agent_admin'),
    path('chaining/', include('smart_selects.urls')),

    path('home/', tours_views.home, name='home'),
    path('news/', tours_views.NewsListView.as_view(), name='news'),

    # ========== API ДЛЯ КАЛЕНДАРЯ ==========
    # ШВИДКИЙ API (ДЕМО-ДАНІ) - РЕКОМЕНДОВАНИЙ
    path('api/calendar-prices/', tours_views.calendar_prices_otpusk, name='calendar_prices'),

    # РЕАЛЬНИЙ API (ПОВІЛЬНИЙ, АЛЕ РЕАЛЬНІ ЦІНИ)
    path('api/calendar-prices-otpusk/', tours_views.calendar_prices_from_otpusk, name='calendar_prices_otpusk'),

    path('get-cities/', tours_views.get_cities, name='get_cities'),
    path('api/chat/', tours_views.chat_api, name='chat_api'),
    path('api/popular-tours/', tours_views.popular_tours_api, name='popular_tours_api'),

    path('api/hotel-reviews/', tours_views.hotel_reviews_api, name='hotel_reviews_api'),
    path('a/<slug:slug>/api/hotel-reviews/', tours_views.hotel_reviews_api, name='agent_hotel_reviews_api'),

    path('consultation-ajax/', tours_views.consultation_ajax, name='consultation_ajax'),
    path('a/<slug:slug>/consultation-ajax/', tours_views.consultation_ajax, name='agent_consultation_ajax'),

    path('booking-ajax/', tours_views.booking_ajax, name='booking_ajax'),
    path('a/<slug:slug>/booking-ajax/', tours_views.booking_ajax, name='agent_booking_ajax'),

    path('search-otpusk/', tours_views.search_otpusk, name='search_otpusk'),
    path('a/<slug:slug>/search-otpusk/', tours_views.search_otpusk, name='agent_search_otpusk'),

    path('search-otpusk-by-country/', tours_views.search_otpusk_by_country, name='search_otpusk_by_country'),
    path('a/<slug:slug>/search-otpusk-by-country/', tours_views.search_otpusk_by_country,
         name='agent_search_otpusk_by_country'),

    path('tour-detail/', tours_views.tour_detail_otpusk, name='tour_detail_otpusk'),
    path('a/<slug:slug>/tour-detail/', tours_views.tour_detail_otpusk, name='agent_tour_detail_otpusk'),

    path('consultation/', TemplateView.as_view(template_name='tours/consultation_form.html'), name='consultation'),

    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    path('privacy-policy/', landing_views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', landing_views.terms_of_service, name='terms_of_service'),
    path('tours-by-city/', tours_views.tours_by_city, name='tours_by_city'),
    path('city/<int:city_id>/', tours_views.city_detail, name='city_detail'),

    path('constructor/', include('constructor.urls')),

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)