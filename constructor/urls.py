from django.urls import path, include
from . import views

app_name = 'constructor'

urlpatterns = [
    path('register/', views.agent_register_step1, name='register'),
    path('verify/', views.agent_verify, name='verify'),
    path('dashboard/', views.constructor_dashboard, name='dashboard'),
    path('open-site/', views.open_site, name='open_site'),
    path('generate-image/', views.generate_image, name='generate_image'),
]

# окремий конфіг для агентських сайтів
agent_urlpatterns = [
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