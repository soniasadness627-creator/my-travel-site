from django.contrib import admin
from django import forms
from django.db import models
from django.contrib.auth import get_user_model
from .models import (
    Tour, Booking, News, TourImage, Review, Consultation,
    PriceOption, AmenityCategory, Amenity, City, DepartureCity, PopularDestination,
    NewsImage, TourPriceByTourists, CountryInfo, PriceCalendar, AmenityName, PopularHotel
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


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('get_author_name', 'rating', 'comment_preview', 'created_at')
    can_delete = True
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
        return request.user.is_superuser


# ========== ФОРМА ДЛЯ ТУРУ ==========
class TourAdminForm(forms.ModelForm):
    country = forms.ChoiceField(
        choices=[('', '---------')] + [('Україна', 'Україна'), ('Єгипет', 'Єгипет'), ('Туреччина', 'Туреччина'),
                                       ('Іспанія', 'Іспанія'), ('Греція', 'Греція'), ('Італія', 'Італія')],
        label="Країна",
        required=True,
        help_text="Оберіть країну зі списку"
    )

    stars = forms.ChoiceField(
        choices=[('', '---------'), ('1', '1*'), ('2', '2*'), ('3', '3*'), ('4', '4*'), ('5', '5*')],
        label="Категорія готелю (зірки)",
        required=False,
        help_text="Виберіть категорію готелю"
    )

    class Meta:
        model = Tour
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.stars:
            self.fields['stars'].initial = str(self.instance.stars)

        if self.instance and self.instance.pk:
            self.fields['country'].initial = self.instance.country

        cities = DepartureCity.objects.all().order_by('country', 'name')
        choices = [('', '---------')] + [(city.name, f"{city.name} ({city.country}, {city.get_transport_display()})")
                                         for city in cities]
        self.fields['departure_city'] = forms.ChoiceField(
            choices=choices,
            required=False,
            label="Місто виїзду",
            help_text="Оберіть місто вильоту зі списку (або залиште порожнім)"
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.country = self.cleaned_data['country']

        stars_value = self.cleaned_data.get('stars')
        if stars_value and stars_value != '':
            instance.stars = int(stars_value)
        else:
            instance.stars = None

        if commit:
            instance.save()
        return instance


# ========== АДМІНКИ З РОЗМЕЖУВАННЯМ ПРАВ ==========

@admin.register(CountryInfo)
class CountryInfoAdmin(admin.ModelAdmin):
    list_display = ('country',)
    search_fields = ('country',)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at', 'agent', 'is_processed')
    list_filter = ('created_at', 'is_processed')
    search_fields = ('name', 'phone', 'comment')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(agent=request.user)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.agent:
            obj.agent = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.agent != request.user:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    form = TourAdminForm
    list_display = ("title", "country", "city", "stars", "price", "is_popular", "duration",
                    "room_type", "meal_type", "start_date", "departure_city", "transport", "author")
    list_filter = ("country", "city", "stars", "start_date", "author", "transport", "meal_type", "is_popular")
    search_fields = ("title", "country", "city__name", "description")
    readonly_fields = ("created_at",)
    filter_horizontal = ['amenities']
    inlines = [TourImageInline, ReviewInline, BookingInline]

    fieldsets = (
        ("Основна інформація", {
            "fields": ("title", "description", "country", "city", "price", "stars", "map_url", "amenities",
                       "is_popular")
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
        return qs.filter(author=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author" and not request.user.is_superuser:
            kwargs["initial"] = request.user
            kwargs["queryset"] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.author != request.user:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.author != request.user:
            return False
        return True


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
        return qs.filter(author=request.user)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.author != request.user:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ========== РЕЄСТРАЦІЯ ДЛЯ СУПЕРАДМІНА (БРОНЮВАННЯ ТА КОНСУЛЬТАЦІЇ) ==========

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'email', 'get_tour_info', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'email', 'message')
    readonly_fields = ('created_at',)
    list_per_page = 20

    def get_tour_info(self, obj):
        """Показує інформацію про тур з повідомлення"""
        if obj.message:
            for line in obj.message.split('\n'):
                if line.startswith('Тур:'):
                    return line.replace('Тур:', '').strip()[:50]
        return '—'

    get_tour_info.short_description = 'Тур'

    def has_add_permission(self, request):
        return False


# Якщо Consultation ще не зареєстрований, додайте:
@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'email', 'created_at', 'is_processed', 'agent')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('name', 'phone', 'email', 'comment')
    readonly_fields = ('created_at',)
    list_editable = ('is_processed',)
    list_per_page = 20

    def has_add_permission(self, request):
        return False

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_tour_title', 'get_author_name', 'rating', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at', 'tour')
    search_fields = ('comment', 'guest_name', 'user__username', 'tour__title')
    readonly_fields = ('created_at',)
    list_per_page = 20

    def get_tour_title(self, obj):
        return obj.tour.title

    get_tour_title.short_description = 'Тур'

    def get_author_name(self, obj):
        if obj.user:
            return obj.user.username
        return obj.guest_name or 'Гість'

    get_author_name.short_description = 'Автор'

    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment

    comment_preview.short_description = 'Коментар'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(tour__author=request.user)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PriceOption)
class PriceOptionAdmin(admin.ModelAdmin):
    list_display = ('tour', 'departure_date', 'duration', 'departure_city', 'room_type', 'meal_type', 'price',
                    'is_available')
    list_filter = ('tour', 'departure_city', 'is_available')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_available')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(tour__author=request.user)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.tour and obj.tour.author != request.user:
            return False
        return True


@admin.register(TourPriceByTourists)
class TourPriceByTouristsAdmin(admin.ModelAdmin):
    list_display = ('tour', 'adults', 'infants', 'children_2_3', 'children_4_10', 'children_11_16', 'price',
                    'is_default')
    list_filter = ('tour', 'adults', 'is_default')
    search_fields = ('tour__title',)
    list_editable = ('price', 'is_default')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(tour__author=request.user)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and obj.tour and obj.tour.author != request.user:
            return False
        return True


@admin.register(PriceCalendar)
class PriceCalendarAdmin(admin.ModelAdmin):
    list_display = ('country', 'departure_city', 'date', 'duration', 'price', 'is_available')
    list_filter = ('country', 'departure_city', 'is_available')
    search_fields = ('country', 'departure_city')
    list_editable = ('price', 'is_available')
    list_per_page = 50

    fieldsets = (
        ('Інформація про тур', {
            'fields': ('country', 'departure_city', 'date', 'duration', 'price', 'is_available')
        }),
    )

    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="price_calendar_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['country', 'departure_city', 'date', 'duration', 'price'])

        for item in queryset:
            writer.writerow([item.country, item.departure_city, item.date, item.duration, item.price])

        self.message_user(request, f"Експортовано {queryset.count()} записів")
        return response

    export_as_csv.short_description = "📥 Експортувати вибрані ціни в CSV"


@admin.register(PopularDestination)
class PopularDestinationAdmin(admin.ModelAdmin):
    list_display = ('country', 'order')
    list_editable = ('order',)
    search_fields = ('country',)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AmenityCategory)
class AmenityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    list_editable = ['order']
    fields = ('name', 'order')

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order', 'is_popular']
    list_filter = ['category', 'is_popular']
    search_fields = ['name__name']
    list_editable = ['order', 'is_popular']
    fields = ('category', 'name', 'order', 'is_popular')

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
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

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AmenityName)
class AmenityNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order', 'is_popular_default')
    list_filter = ('category',)
    search_fields = ('name',)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ========== АДМІНКА ДЛЯ ПОПУЛЯРНИХ ГОТЕЛІВ (ТІЛЬКИ СУПЕРАДМІН) ==========
@admin.register(PopularHotel)
class PopularHotelAdmin(admin.ModelAdmin):
    list_display = ('hotel_name', 'country', 'city', 'rating', 'reviews_count', 'price', 'od', 'ol', 'order',
                    'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('hotel_name', 'country', 'city', 'hid', 'oid')
    list_per_page = 20

    fieldsets = (
        ('Основна інформація', {
            'fields': ('hid', 'oid', 'hotel_name', 'country', 'city')
        }),
        ('Рейтинг та ціна', {
            'fields': ('rating', 'reviews_count', 'price')
        }),
        ('Дати та тривалість', {
            'fields': ('od', 'ol')
        }),
        ('Фото', {
            'fields': ('image', 'image_url')
        }),
        ('Налаштування', {
            'fields': ('order', 'is_active')
        }),
    )

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ========== МАСОВА EMAIL-РОЗСИЛКА ==========
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.contrib.admin import AdminSite
import requests
import csv
import io


class MassEmailAdminSite(AdminSite):
    site_header = "Масова email-розсилка"
    site_title = "Mass Email"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_view(self.mass_email_view), name='mass_email'),
            path('send/', self.admin_view(self.send_mass_email), name='send_mass_email'),
        ]
        return custom_urls + urls

    def mass_email_view(self, request):
        if not request.user.is_superuser:
            messages.error(request, "Доступ тільки для суперадміна")
            return redirect('/admin/')

        agents_count = User.objects.filter(is_agent=True).count()
        agents = User.objects.filter(is_agent=True).values_list('email', 'username')[:20]

        context = {
            'agents_count': agents_count,
            'agents_preview': agents,
            'title': 'Масова email-розсилка',
        }
        return render(request, 'admin/mass_email.html', context)

    def send_mass_email(self, request):
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Access denied'}, status=403)

        if request.method == 'POST':
            subject = request.POST.get('subject', '')
            message = request.POST.get('message', '')
            recipient_type = request.POST.get('recipient_type', 'all_agents')
            uploaded_file = request.FILES.get('email_file')

            emails = []

            if recipient_type == 'all_agents':
                emails = list(User.objects.filter(is_agent=True, email__isnull=False)
                              .exclude(email='')
                              .values_list('email', flat=True))
            elif recipient_type == 'upload_file' and uploaded_file:
                content = uploaded_file.read().decode('utf-8')
                if uploaded_file.name.endswith('.csv'):
                    reader = csv.reader(io.StringIO(content))
                    for row in reader:
                        if row and '@' in row[0]:
                            emails.append(row[0].strip())
                else:
                    for line in content.splitlines():
                        if '@' in line:
                            emails.append(line.strip())

            if not emails:
                messages.error(request, 'Не знайдено email для розсилки')
                return redirect('/admin/mass-email/')

            success_count = 0
            fail_count = 0

            # ← ВИДАЛИТИ [:50], ОСЬ ТУТ!
            for email in emails:  # ← БЕЗ [:50]
                result = self.send_via_mailgun(email, subject, message)
                if result:
                    success_count += 1
                else:
                    fail_count += 1

            messages.success(request, f'Відправлено {success_count} листів, помилок: {fail_count}')
            return redirect('/admin/mass-email/')

        return redirect('/admin/mass-email/')

    def send_via_mailgun(self, to_email, subject, message):
        if not settings.MAILGUN_API_KEY:
            return False
        try:
            response = requests.post(
                f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
                auth=("api", settings.MAILGUN_API_KEY),
                data={
                    "from": settings.MAILGUN_FROM_EMAIL,
                    "to": [to_email],
                    "subject": subject,
                    "html": message.replace('\n', '<br>')
                },
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Помилка Mailgun: {e}")
            return False


# Створюємо екземпляр
mass_email_admin = MassEmailAdminSite(name='mass_email')