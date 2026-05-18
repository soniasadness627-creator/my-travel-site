from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    # Головна сторінка лендингу
    path('', views.index, name='index'),

    # Сторінка політики конфіденційності
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),

    # Сторінка правил надання послуг
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),

    # AJAX ендпоінт для обробки форми зворотного зв'язку (Telegram сповіщення)
    path('contact-ajax/', views.landing_contact_ajax, name='contact_ajax'),
]