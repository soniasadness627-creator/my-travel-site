from django.contrib import admin
from tours.models import (
    Tour, Booking, PriceOption, Review, Consultation, News,
    TourPriceByTourists, CountryInfo, PriceCalendar, PopularDestination
)


# ========== ПРОСТІ АДМІН-КЛАСИ ДЛЯ ВСІХ МОДЕЛЕЙ ==========

class TourAdmin(admin.ModelAdmin):
    list_display = ("title", "country", "price", "start_date")
    list_filter = ("country", "start_date")
    search_fields = ("title", "country")


class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tour_title', 'name', 'phone', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'email')

    def get_tour_title(self, obj):
        return obj.tour.title
    get_tour_title.short_description = 'Тур'


class PriceOptionAdmin(admin.ModelAdmin):
    list_display = ('tour', 'departure_date', 'duration', 'departure_city', 'price', 'is_available')
    list_filter = ('departure_city', 'is_available')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_available')


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tour_title', 'get_author_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('comment',)

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


class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "text")


class CountryInfoAdmin(admin.ModelAdmin):
    list_display = ('country',)
    search_fields = ('country',)


class PriceCalendarAdmin(admin.ModelAdmin):
    list_display = ('tour', 'date', 'duration', 'price')
    list_filter = ('tour', 'date')
    search_fields = ('tour__title',)


class PopularDestinationAdmin(admin.ModelAdmin):
    list_display = ('country', 'order')
    list_editable = ('order',)
    search_fields = ('country',)


class TourPriceByTouristsAdmin(admin.ModelAdmin):
    list_display = ('tour', 'adults', 'children_2_3', 'children_4_10', 'children_11_16', 'price', 'is_default')
    list_filter = ('tour', 'adults', 'is_default')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_default')


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