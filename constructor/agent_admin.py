from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from tours.models import (
    Tour, Booking, PriceOption, Review, Consultation, News,
    TourPriceByTourists, CountryInfo, PriceCalendar, PopularDestination
)
from django.contrib.auth import get_user_model

User = get_user_model()


class AgentAdminSite(AdminSite):
    site_header = "Панель керування агента"
    site_title = "Агентська адмінка"
    index_title = "Ласкаво просимо до вашого кабінету"

    def has_permission(self, request):
        return request.user.is_authenticated and request.user.is_agent

    def get_urls(self):
        urls = super().get_urls()
        wrapper = self.admin_view
        return [
            path('', wrapper(self.index), name='index'),
            path('login/', self.login, name='login'),
            path('logout/', self.logout, name='logout'),
            path('password_change/', self.password_change, name='password_change'),
            path('password_change/done/', self.password_change_done, name='password_change_done'),
            path('jsi18n/', self.i18n_javascript, name='jsi18n'),
        ] + urls[4:]


agent_admin_site = AgentAdminSite(name='agent_admin')


# ========== БАЗОВА РЕЄСТРАЦІЯ ВСІХ МОДЕЛЕЙ (без кастомних класів для початку) ==========
# Це гарантовано покаже всі моделі в адмінці

agent_admin_site.register(Tour)
agent_admin_site.register(Booking)
agent_admin_site.register(PriceOption)
agent_admin_site.register(Review)
agent_admin_site.register(Consultation)
agent_admin_site.register(News)
agent_admin_site.register(CountryInfo)
agent_admin_site.register(PriceCalendar)
agent_admin_site.register(PopularDestination)
agent_admin_site.register(TourPriceByTourists)