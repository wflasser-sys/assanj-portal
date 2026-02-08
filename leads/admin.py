from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'business_name', 'phone_number', 'category', 'status', 'assigned_sales_closer', 'created_by', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('business_name', 'phone_number')
