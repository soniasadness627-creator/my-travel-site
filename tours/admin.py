from django.contrib import admin
from django import forms
from django.db import models
from django.contrib.auth import get_user_model
from .models import (
    Tour, Booking, News, TourImage, Review, Consultation,
    PriceOption, AmenityCategory, Amenity, City, DepartureCity, PopularDestination,
    NewsImage, TourPriceByTourists, CountryInfo, PriceCalendar, AmenityName  # Додано PriceCalendar, AmenityName
)

User = get_user_model()


# ---------- ДОПОМІЖНІ КЛАСИ ----------
class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 3
    verbose_name = "Додаткове фото"
    verbose_name_plural = "Додаткові фото"


class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 3
    verbose_name = "Додаткове фото"
    verbose_name_plural = "Додаткові фото"


class BookingInline(admin.TabularInline):
    """Відображення бронювань в турі"""
    model = Booking
    extra = 0
    readonly_fields = ('name', 'phone', 'email', 'message', 'created_at')
    can_delete = False
    fields = ('name', 'phone', 'email', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ========== ТИМЧАСОВО ЗАКОМЕНТОВАНО ДЛЯ МІГРАЦІЙ ==========
# class TourAdminForm(forms.ModelForm):
#     country = forms.ChoiceField(
#         choices=[('', '---------')] + [(c, c) for c in
#                                        City.objects.values_list('country', flat=True).distinct().order_by('country')],
#         label="Країна",
#         required=True,
#         help_text="Оберіть країну зі списку"
#     )
#
#     stars = forms.ChoiceField(
#         choices=[('', '---------'), ('1', '1*'), ('2', '2*'), ('3', '3*'), ('4', '4*'), ('5', '5*')],
#         label="Категорія готелю (зірки)",
#         required=False,
#         help_text="Виберіть категорію готелю"
#     )
#
#     class Meta:
#         model = Tour
#         fields = '__all__'
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#
#         if self.instance and self.instance.pk and self.instance.stars:
#             self.fields['stars'].initial = str(self.instance.stars)
#
#         if self.instance and self.instance.pk:
#             self.fields['country'].initial = self.instance.country
#
#         cities = DepartureCity.objects.all().order_by('country', 'name')
#         choices = [('', '---------')] + [(city.name, f"{city.name} ({city.country}, {city.get_transport_display()})")
#                                          for city in cities]
#         self.fields['departure_city'] = forms.ChoiceField(
#             choices=choices,
#             required=False,
#             label="Місто виїзду",
#             help_text="Оберіть місто вильоту зі списку (або залиште порожнім)"
#         )
#
#         if 'author' in self.fields:
#             request = getattr(self, 'request', None)
#             if request and request.user.is_authenticated and not request.user.is_superuser:
#                 self.fields['author'].queryset = User.objects.filter(pk=request.user.pk)
#                 if self.instance and self.instance.pk and self.instance.author != request.user:
#                     self.fields['author'].disabled = True
#
#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         instance.country = self.cleaned_data['country']
#
#         stars_value = self.cleaned_data.get('stars')
#         if stars_value and stars_value != '':
#             instance.stars = int(stars_value)
#         else:
#             instance.stars = None
#
#         if commit:
#             instance.save()
#         return instance


# ========== АДМІНКИ З ПРАВИЛЬНИМИ ОБМЕЖЕННЯМИ ==========

@admin.register(CountryInfo)
class CountryInfoAdmin(admin.ModelAdmin):
    list_display = ('country',)
    search_fields = ('country',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'comment')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs.filter(agent=request.user)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if hasattr(obj, 'agent') and obj.agent:
                return obj.agent == request.user
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if hasattr(obj, 'agent') and obj.agent:
                return obj.agent == request.user
            return False
        return False

    def has_add_permission(self, request):
        return False


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('get_author_name', 'rating', 'comment_preview', 'created_at')
    can_delete = True
    show_change_link = True
    fields = ('get_author_name', 'rating', 'comment_preview', 'created_at')

    def get_author_name(self, obj):
        if obj.user:
            return obj.user.username
        return obj.guest_name or 'Гість'

    get_author_name.short_description = 'Автор'

    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment

    comment_preview.short_description = 'Коментар'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return False
        if request.user.is_superuser:
            return True
        if request.user.is_agent and hasattr(obj, 'tour') and obj.tour:
            return obj.tour.author == request.user
        return False


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    # ТИМЧАСОВО БЕЗ FORM (щоб уникнути помилок)
    # form = TourAdminForm  # ЗАКОМЕНТОВАНО
    list_display = ("title", "country", "city", "stars", "price", "is_popular", "duration", "room_type", "meal_type",
                    "start_date", "departure_city", "transport", "author")
    list_filter = ("country", "city", "stars", "start_date", "author", "transport", "meal_type", "is_popular")
    search_fields = ("title", "country", "city__name", "description")
    readonly_fields = ("created_at",)
    filter_horizontal = ['amenities']
    inlines = [TourImageInline, ReviewInline, BookingInline]

    fieldsets = (
        ("Основна інформація", {
            "fields": ("title", "description", "country", "city", "price", "stars", "map_url", "amenities", "is_popular")
        }),
        ("Дати", {
            "fields": ("start_date", "end_date")
        }),
        ("Параметри туру", {
            "fields": ("duration", "room_type", "meal_type")
        }),
        ("Виліт", {
            "fields": ("departure_city", "transport")
        }),
        ("Медіа", {
            "fields": ("image",)
        }),
        ("Автор", {
            "fields": ("author",)
        }),
        ("Службова інформація", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs.filter(author=request.user)
        return qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return self.has_add_permission(request)
        if request.user.is_superuser:
            return True
        if request.user.is_agent:
            if obj:
                return obj.author == request.user
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_agent:
            if obj:
                return obj.author == request.user
            return False
        return False

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        if request.user.is_agent:
            return True
        return False


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    list_filter = ("created_at", "author")
    search_fields = ("title", "text")
    readonly_fields = ("created_at",)
    inlines = [NewsImageInline]
    fieldsets = (
        (None, {"fields": ("title", "text", "image", "author")}),
        ("Службова інформація", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs.filter(author=request.user)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            if not request.user.is_superuser:
                kwargs["queryset"] = User.objects.filter(pk=request.user.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return self.has_add_permission(request)
        if request.user.is_superuser:
            return True
        if request.user.is_agent:
            if obj:
                return obj.author == request.user
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_agent:
            if obj:
                return obj.author == request.user
            return False
        return False

    def has_add_permission(self, request):
        if request.user.is_superuser or request.user.is_agent:
            return True
        return False

    def save_model(self, request, obj, form, change):
        if not obj.pk and not request.user.is_superuser:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tour_title', 'name', 'phone', 'email', 'created_at')
    list_filter = ('created_at', 'tour')
    search_fields = ('name', 'phone', 'email', 'tour__title')
    readonly_fields = ('created_at',)
    list_per_page = 20

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs.filter(tour__author=request.user)
        return qs.none()

    def get_tour_title(self, obj):
        return obj.tour.title

    get_tour_title.short_description = 'Тур'
    get_tour_title.admin_order_field = 'tour__title'

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if obj:
                return obj.tour.author == request.user
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if obj:
                return obj.tour.author == request.user
            return False
        return False

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.is_agent:
            return True
        return False

    def has_add_permission(self, request):
        return False

    fieldsets = (
        ('Інформація про бронювання', {
            'fields': ('tour', 'name', 'phone', 'email', 'message')
        }),
        ('Службова інформація', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tour_title', 'get_author_name', 'rating', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at', 'tour')
    search_fields = ('comment', 'guest_name', 'user__username', 'tour__title')
    readonly_fields = ('created_at',)
    list_per_page = 20

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs.filter(tour__author=request.user)
        return qs.none()

    def get_tour_title(self, obj):
        return obj.tour.title

    get_tour_title.short_description = 'Тур'
    get_tour_title.admin_order_field = 'tour__title'

    def get_author_name(self, obj):
        if obj.user:
            return obj.user.username
        return obj.guest_name or 'Гість'

    get_author_name.short_description = 'Автор'
    get_author_name.admin_order_field = 'user__username'

    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment

    comment_preview.short_description = 'Коментар'

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if obj:
                return obj.tour.author == request.user
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if obj:
                return obj.tour.author == request.user
            return False
        return False

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.is_agent:
            return True
        return False

    def has_add_permission(self, request):
        return False

    fieldsets = (
        ('Інформація про відгук', {
            'fields': ('tour', 'rating', 'comment')
        }),
        ('Автор', {
            'fields': ('user', 'guest_name')
        }),
        ('Службова інформація', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PriceOption)
class PriceOptionAdmin(admin.ModelAdmin):
    list_display = ('tour', 'departure_date', 'duration', 'departure_city', 'room_type', 'meal_type', 'price',
                    'is_available')
    list_filter = ('tour', 'departure_city', 'is_available')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_available')
    fieldsets = (
        ('Тур', {'fields': ('tour', 'departure_date', 'duration', 'departure_city', 'room_type', 'meal_type')}),
        ('Ціна', {'fields': ('price', 'is_available')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs.filter(tour__author=request.user)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if obj:
                return obj.tour.author == request.user
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if obj:
                return obj.tour.author == request.user
            return False
        return False

    def has_add_permission(self, request):
        if request.user.is_superuser or request.user.is_agent:
            return True
        return False


@admin.register(TourPriceByTourists)
class TourPriceByTouristsAdmin(admin.ModelAdmin):
    list_display = ('tour', 'adults', 'infants', 'children_2_3', 'children_4_10', 'children_11_16', 'price',
                    'is_default')
    list_filter = ('tour', 'adults', 'is_default')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_default')
    fieldsets = (
        ('Тур', {'fields': ('tour',)}),
        ('Склад туристів', {'fields': ('adults', 'infants', 'children_2_3', 'children_4_10', 'children_11_16')}),
        ('Ціна', {'fields': ('price', 'is_default')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs.filter(tour__author=request.user)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if obj:
                return obj.tour.author == request.user
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        if request.user.is_agent:
            if obj:
                return obj.tour.author == request.user
            return False
        return False

    def has_add_permission(self, request):
        if request.user.is_superuser or request.user.is_agent:
            return True
        return False


@admin.register(PopularDestination)
class PopularDestinationAdmin(admin.ModelAdmin):
    list_display = ('country', 'order')
    list_editable = ('order',)
    search_fields = ('country',)
    list_filter = ('order',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


@admin.register(AmenityCategory)
class AmenityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    list_editable = ['order']
    fields = ('name', 'order')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order', 'is_popular']
    list_filter = ['category', 'is_popular']
    search_fields = ['name__name']
    list_editable = ['order', 'is_popular']
    fields = ('category', 'name', 'order', 'is_popular')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


class AmenityInline(admin.TabularInline):
    model = Amenity
    extra = 1
    fields = ['name', 'order', 'is_popular']
    show_change_link = True


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    list_filter = ('country',)
    search_fields = ('name', 'country')
    ordering = ('country', 'name')
    fieldsets = (
        (None, {'fields': ('name', 'country')}),
        ('Додаткова інформація', {'fields': ('description', 'activities', 'sights'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


@admin.register(DepartureCity)
class DepartureCityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'get_transport_display')
    list_filter = ('country', 'transport')
    search_fields = ('name', 'country')
    ordering = ('country', 'name')

    def get_transport_display(self, obj):
        return obj.get_transport_display()

    get_transport_display.short_description = 'Транспорт'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_agent:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


# ========== ДОДАТКОВІ МОДЕЛІ ДЛЯ СУПЕРАДМІНА ==========

@admin.register(PriceCalendar)
class PriceCalendarAdmin(admin.ModelAdmin):
    list_display = ('tour', 'date', 'duration', 'price')
    list_filter = ('tour', 'date')
    search_fields = ('tour__title',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser


@admin.register(AmenityName)
class AmenityNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order', 'is_popular_default')
    list_filter = ('category',)
    search_fields = ('name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser