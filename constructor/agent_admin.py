from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from tours.models import (
    Booking, Consultation, News, HotelReview
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
        from tours.models import City
        cities = City.objects.filter(country=country).order_by('name').values('id', 'name')
        return JsonResponse(list(cities), safe=False)
    return JsonResponse([], safe=False)


# ========== АДМІН-КЛАСИ ДЛЯ АГЕНТІВ ==========

class AgentBookingAdmin(admin.ModelAdmin):
    """Адмінка для бронювань - показує ТІЛЬКИ бронювання поточного агента"""
    list_display = ('id', 'name', 'phone', 'email', 'get_tour_info', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone', 'email', 'message')
    readonly_fields = ('created_at',)
    list_per_page = 20

    def get_queryset(self, request):
        """Фільтрує бронювання тільки для поточного агента"""
        qs = super().get_queryset(request)
        if request.user.is_agent and not request.user.is_superuser:
            return qs.filter(agent=request.user)
        return qs

    def get_tour_info(self, obj):
        """Показує інформацію про тур з повідомлення"""
        if obj.message:
            for line in obj.message.split('\n'):
                if line.startswith('Тур:'):
                    return line.replace('Тур:', '').strip()[:50]
        return '—'

    get_tour_info.short_description = 'Тур'

    def has_add_permission(self, request):
        """Забороняє додавати бронювання вручну"""
        return False

    def has_change_permission(self, request, obj=None):
        """Дозволяє змінювати тільки суперадміну"""
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        """Дозволяє видаляти тільки суперадміну"""
        return request.user.is_superuser


class AgentConsultationAdmin(admin.ModelAdmin):
    """Адмінка для консультацій - показує ТІЛЬКИ заявки поточного агента"""
    list_display = ('id', 'name', 'phone', 'email', 'created_at', 'is_processed')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('name', 'phone', 'email', 'comment')
    readonly_fields = ('created_at',)
    list_editable = ('is_processed',)
    list_per_page = 20

    def get_queryset(self, request):
        """Фільтрує заявки тільки для поточного агента"""
        qs = super().get_queryset(request)
        if request.user.is_agent and not request.user.is_superuser:
            return qs.filter(agent=request.user)
        return qs

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class AgentHotelReviewAdmin(admin.ModelAdmin):
    """Адмінка для відгуків про готелі - показує ТІЛЬКИ відгуки поточного агента"""
    list_display = ('id', 'guest_name', 'rating', 'get_rating_stars', 'created_at', 'is_approved')
    list_filter = ('rating', 'created_at', 'is_approved')
    search_fields = ('guest_name', 'comment', 'hid')
    list_display_links = ('id', 'guest_name')
    list_editable = ('is_approved',)
    readonly_fields = ('hid', 'oid', 'guest_name', 'rating', 'comment', 'created_at', 'agent')

    def get_rating_stars(self, obj):
        stars = ''
        for i in range(5):
            if i < obj.rating:
                stars += '★'
            else:
                stars += '☆'
        return stars

    get_rating_stars.short_description = 'Оцінка'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_agent and not request.user.is_superuser:
            return qs.filter(agent=request.user)
        return qs

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class AgentNewsAdmin(admin.ModelAdmin):
    """Адмінка для новин - показує ТІЛЬКИ новини поточного агента"""
    list_display = ("title", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "text")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_agent and not request.user.is_superuser:
            return qs.filter(author=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


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

# ========== РЕЄСТРАЦІЯ ТІЛЬКИ ПОТРІБНИХ МОДЕЛЕЙ ==========
agent_admin_site.register(Booking, AgentBookingAdmin)           # Бронювання
agent_admin_site.register(Consultation, AgentConsultationAdmin) # Заявки на консультацію
agent_admin_site.register(HotelReview, AgentHotelReviewAdmin)   # Відгуки про готелі
agent_admin_site.register(News, AgentNewsAdmin)                 # Новини

# ========== ДІАГНОСТИКА ==========
print("=" * 50)
print("АГЕНТСЬКА АДМІНКА - УСПІШНО ЗАРЕЄСТРОВАНО")
print("Зареєстровані моделі: Booking, Consultation, HotelReview, News")
print("=" * 50)