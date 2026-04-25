from django.contrib import admin
from django.contrib.admin import AdminSite
from tours.models import Tour, Booking, PriceOption, Review, Consultation, News, TourPriceByTourists

class AgentAdminSite(AdminSite):
    site_header = "Панель керування агента"
    site_title = "Агентська адмінка"
    index_title = "Ласкаво просимо до вашого кабінету"

    def has_permission(self, request):
        # ТІЛЬКИ агенти можуть заходити сюди!
        return request.user.is_authenticated and request.user.is_agent

agent_admin_site = AgentAdminSite(name='agent_admin')

# Реєструємо ТІЛЬКИ ті моделі, які потрібні агенту
agent_admin_site.register(Tour)
agent_admin_site.register(Booking)
agent_admin_site.register(PriceOption)
agent_admin_site.register(Review)
agent_admin_site.register(Consultation)
agent_admin_site.register(News)
agent_admin_site.register(TourPriceByTourists)