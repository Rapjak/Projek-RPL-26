from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RoleChoices


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('npm_nip', 'name', 'email', 'role', 'unit_gedung', 'total_poin', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_staff', 'role')
    search_fields = ('npm_nip', 'name', 'email', 'unit_gedung')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')

    fieldsets = (
        (None, {'fields': ('id', 'npm_nip', 'name', 'email', 'password')}),
        ('Peran & Lokasi', {'fields': ('role', 'unit_gedung')}),
        ('Poin', {'fields': ('total_poin',)}),
        ('Status', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Timestamps', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('npm_nip', 'name', 'email', 'unit_gedung', 'role', 'password1', 'password2'),
        }),
    )

    filter_horizontal = ()
