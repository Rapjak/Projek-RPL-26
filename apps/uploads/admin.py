from django.contrib import admin
from .models import Upload


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'file_size', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__npm_nip', 'user__name', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'error_message')
