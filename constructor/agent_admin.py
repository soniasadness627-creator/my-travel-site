from django.contrib import admin
from django.contrib.admin import AdminSite
from tours.models import Tour, Booking, PriceOption, Review, Consultation, News, TourPriceByTourists, CountryInfo, PriceCalendar, PopularDestination
from django.contrib.auth import get_user_model

User = get_user_model()


class AgentAdminSite(AdminSite):
    site_header = "Панель керування агента"
    site_title = "Агентська адмінка"
    index_title = "Ласкаво просимо до вашого кабінету"

    def has_permission(self, request):
        return request.user.is_authenticated and request.user.is_agent


agent_admin_site = AgentAdminSite(name='agent_admin')


# ========== КАСТОМНІ АДМІН-КЛАСИ ДЛЯ АГЕНТІВ ==========

class AgentTourAdmin(admin.ModelAdmin):
    list_display = ("title", "country", "price", "start_date", "author")
    list_filter = ("country", "start_date")
    search_fields = ("title", "country")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # ТІЛЬКИ тури, створені цим агентом
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
        # ТІЛЬКИ бронювання на тури цього агента
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
    list_display = ('name', 'phone', 'created_at', 'is_processed')
    list_filter = ('created_at', 'is_processed')
    search_fields = ('name', 'phone', 'comment')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # ТІЛЬКИ заявки, які належать цьому агенту
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
        return qs  # Інформація про країни спільна для всіх


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
        return qs  # Популярні напрямки спільні для всіх


class AgentTourPriceByTouristsAdmin(admin.ModelAdmin):
    list_display = ('tour', 'adults', 'children_2_3', 'children_4_10', 'children_11_16', 'price', 'is_default')
    list_filter = ('tour', 'adults', 'is_default')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_default')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)


# ========== РЕЄСТРАЦІЯ МОДЕЛЕЙ ==========

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