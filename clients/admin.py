"""
Admin configuration for Client model.
"""

from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'full_name', 'city', 'created_by', 'date_created')
    list_filter = ('city', 'business_category', 'date_created')
    search_fields = ('full_name', 'business_name', 'email', 'phone')
    readonly_fields = ('date_created',)
