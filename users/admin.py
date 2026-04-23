from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # Столбцы, которые будут отображаться в списке пользователей
    list_display = ('username', 'email', 'is_agent', 'is_staff', 'is_superuser')

    # Поля, которые можно искать в админке
    search_fields = ('username', 'email', 'phone')

    # Поля, по которым можно фильтровать пользователей
    list_filter = ('is_agent', 'is_staff', 'is_superuser', 'is_active')

    # Поля, которые будут отображаться в форме редактирования пользователя
    fieldsets = DjangoUserAdmin.fieldsets + (
        (None, {'fields': ('is_agent', 'phone')}),
    )

    # Поля, которые будут отображаться при создании нового пользователя
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {'fields': ('is_agent', 'phone')}),
    )