from django.contrib import admin
from .models import Registration

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'phone', 'experience_level', 'status', 'created_at')
    list_filter = ('experience_level', 'status', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    list_editable = ('status',)
    ordering = ('-created_at',)

