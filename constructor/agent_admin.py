from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from tours.models import (
    Tour, Booking, PriceOption, Review, Consultation, News,
    TourPriceByTourists, CountryInfo, PriceCalendar, PopularDestination,
    City, DepartureCity
)
from django.contrib.auth import get_user_model

User = get_user_model()


# ========== AJAX ДЛЯ ДИНАМІЧНОГО ЗАВАНТАЖЕННЯ МІСТ ==========
@csrf_exempt
@require_GET
def get_cities_ajax(request):
    """Повертає список міст для вибраної країни"""
    country = request.GET.get('country', '')
    if country:
        cities = City.objects.filter(country=country).order_by('name').values('id', 'name')
        return JsonResponse(list(cities), safe=False)
    return JsonResponse([], safe=False)


# ========== ФОРМА ДЛЯ ТУРУ З ВИПАДАЮЧИМИ СПИСКАМИ ==========
class AgentTourForm(forms.ModelForm):
    # Країна - випадаючий список
    country = forms.ChoiceField(
        choices=[],
        label="Країна",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_country'})
    )

    # Місто - буде ModelChoiceField з динамічним завантаженням
    city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        label="Курорт/місто",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_city'})
    )

    # Місто вильоту - випадаючий список
    departure_city = forms.ModelChoiceField(
        queryset=DepartureCity.objects.all(),
        label="Місто виїзду",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Зірки - випадаючий список
    stars = forms.ChoiceField(
        choices=[('', '---------'), ('1', '1*'), ('2', '2*'), ('3', '3*'), ('4', '4*'), ('5', '5*')],
        label="Категорія (зірки)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Tour
        fields = ['title', 'description', 'country', 'city', 'price',
                  'start_date', 'end_date', 'image', 'map_url', 'departure_city',
                  'transport', 'duration', 'room_type', 'meal_type', 'stars',
                  'is_popular', 'amenities', 'author']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'style': 'width: 100%;'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'map_url': forms.URLInput(attrs={'class': 'form-control'}),
            'transport': forms.Select(attrs={'class': 'form-select'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'room_type': forms.TextInput(attrs={'class': 'form-control'}),
            'meal_type': forms.Select(attrs={'class': 'form-select'}),
            'is_popular': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'amenities': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
            'author': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ========== КРАЇНИ ==========
        countries_from_tours = Tour.objects.values_list('country', flat=True).distinct()
        countries_from_cities = City.objects.values_list('country', flat=True).distinct()
        all_countries = set(list(countries_from_tours) + list(countries_from_cities))

        country_choices = [('', '---------')] + [(c, c) for c in sorted(all_countries) if c]
        self.fields['country'].choices = country_choices

        # ========== МІСТА ==========
        country_value = None
        if self.data and self.data.get('country'):
            country_value = self.data.get('country')
        elif self.instance and self.instance.pk and self.instance.country:
            country_value = self.instance.country

        if country_value:
            self.fields['city'].queryset = City.objects.filter(country=country_value).order_by('name')
            if self.instance and self.instance.pk and self.instance.city:
                self.fields['city'].initial = self.instance.city
        else:
            self.fields['city'].queryset = City.objects.none()

        # ========== МІСТО ВИЛЬОТУ ==========
        self.fields['departure_city'].queryset = DepartureCity.objects.all().order_by('country', 'name')
        if self.instance and self.instance.pk and self.instance.departure_city:
            self.fields['departure_city'].initial = self.instance.departure_city

        # ========== АВТОР ==========
        if hasattr(self, 'request') and self.request.user:
            self.fields['author'].initial = self.request.user
            self.fields['author'].widget = forms.HiddenInput()

    def clean_author(self):
        if hasattr(self, 'request'):
            return self.request.user
        return self.cleaned_data.get('author')


# ========== АДМІН-КЛАСИ ДЛЯ АГЕНТІВ ==========

class AgentTourAdmin(admin.ModelAdmin):
    form = AgentTourForm
    list_display = ("title", "country", "city", "price", "start_date", "author")
    list_filter = ("country", "start_date")
    search_fields = ("title", "country", "description")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(author=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    class Media:
        js = ('admin/js/dynamic_city.js',)


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

    def has_add_permission(self, request):
        return False


class AgentPriceOptionAdmin(admin.ModelAdmin):
    list_display = ('tour', 'departure_date', 'duration', 'departure_city', 'price', 'is_available')
    list_filter = ('departure_city', 'is_available')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_available')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tour":
            kwargs["queryset"] = Tour.objects.filter(author=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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

    def has_add_permission(self, request):
        return False


# ========== НАЛАШТУВАННЯ ДЛЯ ЗАЯВОК НА КОНСУЛЬТАЦІЮ (BOOKINGS) ==========
class AgentConsultationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'get_comment_preview', 'created_at', 'is_processed')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('name', 'phone', 'comment')
    list_editable = ('is_processed',)
    readonly_fields = ('created_at',)
    list_per_page = 20

    def get_comment_preview(self, obj):
        """Показує перші 50 символів коментаря"""
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '—'

    get_comment_preview.short_description = 'Коментар'

    def get_queryset(self, request):
        """Фільтрує заявки тільки для поточного агента"""
        qs = super().get_queryset(request)
        return qs.filter(agent=request.user)

    def has_add_permission(self, request):
        """Забороняє додавати заявки вручну"""
        return False

    def has_change_permission(self, request, obj=None):
        """Дозволяє змінювати тільки статус is_processed"""
        return True

    def has_delete_permission(self, request, obj=None):
        """Дозволяє видаляти заявки"""
        return True


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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class AgentPriceCalendarAdmin(admin.ModelAdmin):
    list_display = ('tour', 'date', 'duration', 'price')
    list_filter = ('tour', 'date')
    search_fields = ('tour__title',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tour":
            kwargs["queryset"] = Tour.objects.filter(author=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AgentPopularDestinationAdmin(admin.ModelAdmin):
    list_display = ('country', 'order')
    list_editable = ('order',)
    search_fields = ('country',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class AgentTourPriceByTouristsAdmin(admin.ModelAdmin):
    list_display = ('tour', 'adults', 'children_2_3', 'children_4_10', 'children_11_16', 'price', 'is_default')
    list_filter = ('tour', 'adults', 'is_default')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_default')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(tour__author=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tour":
            kwargs["queryset"] = Tour.objects.filter(author=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AgentCityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country')
    search_fields = ('name', 'country')
    list_filter = ('country',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ========== КАСТОМНИЙ САЙТ АДМІНКИ ==========

class AgentAdminSite(admin.AdminSite):
    site_header = "Панель керування агента"
    site_title = "Агентська адмінка"
    index_title = "Ласкаво просимо до вашого кабінету"

    def has_permission(self, request):
        return request.user.is_authenticated and request.user.is_agent

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get-cities/', self.admin_view(get_cities_ajax), name='get_cities'),
        ]
        return custom_urls + urls


# Створюємо екземпляр агентської адмінки
agent_admin_site = AgentAdminSite(name='agent_admin')

# ========== РЕЄСТРАЦІЯ ВСІХ МОДЕЛЕЙ ==========
agent_admin_site.register(Tour, AgentTourAdmin)
agent_admin_site.register(Booking, AgentBookingAdmin)
agent_admin_site.register(PriceOption, AgentPriceOptionAdmin)
agent_admin_site.register(Review, AgentReviewAdmin)
agent_admin_site.register(Consultation, AgentConsultationAdmin)  # Заявки на консультацію
agent_admin_site.register(News, AgentNewsAdmin)
agent_admin_site.register(CountryInfo, AgentCountryInfoAdmin)
agent_admin_site.register(PriceCalendar, AgentPriceCalendarAdmin)
agent_admin_site.register(PopularDestination, AgentPopularDestinationAdmin)
agent_admin_site.register(TourPriceByTourists, AgentTourPriceByTouristsAdmin)
agent_admin_site.register(City, AgentCityAdmin)

# ========== ДІАГНОСТИКА ==========
print("=" * 50)
print("АГЕНТСЬКА АДМІНКА - УСПІШНО ЗАРЕЄСТРОВАНО")
print(f"Кількість зареєстрованих моделей: {len(agent_admin_site._registry)}")
print("=" * 50)