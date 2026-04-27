from django.contrib import admin
from tours.models import (
    Tour, Booking, PriceOption, Review, Consultation, News,
    TourPriceByTourists, CountryInfo, PriceCalendar, PopularDestination
)


# ========== АДМІН-КЛАСИ З ОБМЕЖЕННЯМИ ДЛЯ АГЕНТІВ ==========

class TourAdmin(admin.ModelAdmin):
    list_display = ("title", "country", "price", "start_date", "author")
    list_filter = ("country", "start_date")
    search_fields = ("title", "country")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(author=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tour_title', 'name', 'phone', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'email')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)

    def get_tour_title(self, obj):
        return obj.tour.title
    get_tour_title.short_description = 'Тур'


class PriceOptionAdmin(admin.ModelAdmin):
    list_display = ('tour', 'departure_date', 'duration', 'departure_city', 'price', 'is_available')
    list_filter = ('departure_city', 'is_available')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_available')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)


class ReviewAdmin(admin.ModelAdmin):
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


class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at', 'is_processed')
    list_filter = ('created_at', 'is_processed')
    search_fields = ('name', 'phone', 'comment')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(agent=request.user)


class NewsAdmin(admin.ModelAdmin):
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


class CountryInfoAdmin(admin.ModelAdmin):
    list_display = ('country',)
    search_fields = ('country',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


class PriceCalendarAdmin(admin.ModelAdmin):
    list_display = ('tour', 'date', 'duration', 'price')
    list_filter = ('tour', 'date')
    search_fields = ('tour__title',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)


class PopularDestinationAdmin(admin.ModelAdmin):
    list_display = ('country', 'order')
    list_editable = ('order',)
    search_fields = ('country',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


class TourPriceByTouristsAdmin(admin.ModelAdmin):
    list_display = ('tour', 'adults', 'children_2_3', 'children_4_10', 'children_11_16', 'price', 'is_default')
    list_filter = ('tour', 'adults', 'is_default')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_default')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)


# ========== РЕЄСТРАЦІЯ ВСІХ МОДЕЛЕЙ ==========

all_models = [
    (Tour, TourAdmin),
    (Booking, BookingAdmin),
    (PriceOption, PriceOptionAdmin),
    (Review, ReviewAdmin),
    (Consultation, ConsultationAdmin),
    (News, NewsAdmin),
    (CountryInfo, CountryInfoAdmin),
    (PriceCalendar, PriceCalendarAdmin),
    (PopularDestination, PopularDestinationAdmin),
    (TourPriceByTourists, TourPriceByTouristsAdmin),
]