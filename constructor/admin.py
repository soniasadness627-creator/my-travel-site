from django.contrib import admin
from .models import AgentSite

@admin.register(AgentSite)
class AgentSiteAdmin(admin.ModelAdmin):
    list_display = ('user', 'slug', 'agency_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'slug', 'agency_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основна інформація', {
            'fields': ('user', 'slug', 'agency_name')
        }),
        ('Дизайн', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_background', 'top_logo', 'bottom_logo', 'enlarge_logo')
        }),
        ('Налаштування', {
            'fields': ('show_news', 'show_operator_logos', 'show_superadmin_tours')
        }),
        ('Кольори', {
            'fields': ('primary_color', 'secondary_color')
        }),
        ('Службова інформація', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )