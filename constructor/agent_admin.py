from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from tours.models import (
    Tour, Booking, PriceOption, Review, Consultation, News,
    TourPriceByTourists, CountryInfo, PriceCalendar, PopularDestination,
    City
)
from django.contrib.auth import get_user_model

User = get_user_model()


# ========== АДМІН-КЛАСИ ДЛЯ АГЕНТІВ ==========

class AgentTourAdmin(admin.ModelAdmin):
    # ВИПРАВЛЕНО: прибрано 'is_active' якщо його немає в моделі
    list_display = ("title", "country", "city", "price", "start_date", "author")
    # ВИПРАВЛЕНО: прибрано 'is_active' з list_filter
    list_filter = ("country", "city", "start_date")
    search_fields = ("title", "country", "city", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(author=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class AgentBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tour_title', 'name', 'phone', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'email')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)

    def get_tour_title(self, obj):
        return obj.tour.title
    get_tour_title.short_description = 'Тур'


class AgentPriceOptionAdmin(admin.ModelAdmin):
    list_display = ('tour', 'departure_date', 'duration', 'departure_city', 'price', 'is_available')
    list_filter = ('departure_city', 'is_available')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_available')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)


class AgentReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tour_title', 'get_author_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)

    def get_tour_title(self, obj):
        return obj.tour.title
    get_tour_title.short_description = 'Тур'

    def get_author_name(self, obj):
        if obj.user:
            return obj.user.username
        return obj.guest_name or 'Гість'
    get_author_name.short_description = 'Автор'


class AgentConsultationAdmin(admin.ModelAdmin):
    # ВИПРАВЛЕНО: прибрано 'email' з list_display (його може не бути в моделі Consultation)
    list_display = ('name', 'phone', 'created_at', 'is_processed')
    list_filter = ('created_at', 'is_processed')
    search_fields = ('name', 'phone', 'comment')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(agent=request.user)


class AgentNewsAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "text")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(author=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class AgentCountryInfoAdmin(admin.ModelAdmin):
    list_display = ('country',)
    search_fields = ('country',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


class AgentPriceCalendarAdmin(admin.ModelAdmin):
    list_display = ('tour', 'date', 'duration', 'price')
    list_filter = ('tour', 'date')
    search_fields = ('tour__title',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)


class AgentPopularDestinationAdmin(admin.ModelAdmin):
    list_display = ('country', 'order')
    list_editable = ('order',)
    search_fields = ('country',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


class AgentTourPriceByTouristsAdmin(admin.ModelAdmin):
    list_display = ('tour', 'adults', 'children_2_3', 'children_4_10', 'children_11_16', 'price', 'is_default')
    list_filter = ('tour', 'adults', 'is_default')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_default')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)


class AgentCityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country')
    search_fields = ('name', 'country')
    list_filter = ('country',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


# ========== КАСТОМНИЙ САЙТ АДМІНКИ ==========

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


# Створюємо екземпляр агентської адмінки
agent_admin_site = AgentAdminSite(name='agent_admin')

# ========== РЕЄСТРАЦІЯ ВСІХ МОДЕЛЕЙ ==========
agent_admin_site.register(Tour, AgentTourAdmin)
agent_admin_site.register(Booking, AgentBookingAdmin)
agent_admin_site.register(PriceOption, AgentPriceOptionAdmin)
agent_admin_site.register(Review, AgentReviewAdmin)
agent_admin_site.register(Consultation, AgentConsultationAdmin)
agent_admin_site.register(News, AgentNewsAdmin)
agent_admin_site.register(CountryInfo, AgentCountryInfoAdmin)
agent_admin_site.register(PriceCalendar, AgentPriceCalendarAdmin)
agent_admin_site.register(PopularDestination, AgentPopularDestinationAdmin)
agent_admin_site.register(TourPriceByTourists, AgentTourPriceByTouristsAdmin)
agent_admin_site.register(City, AgentCityAdmin)

# Додайте ці моделі, якщо вони існують:
try:
    from tours.models import Booking, Consultation, News, CountryInfo, PriceCalendar, PopularDestination, TourPriceByTourists, City
    # Вони вже зареєстровані вище
except ImportError:
    pass

# Додаткові моделі, які можуть бути корисні:
try:
    from users.models import User
    agent_admin_site.register(User, admin.ModelAdmin)
except ImportError:
    pass

try:
    from constructor.models import AgentSite
    agent_admin_site.register(AgentSite, admin.ModelAdmin)
except ImportError:
    pass