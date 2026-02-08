from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'performed_by', 'action', 'entity_type', 'entity_id')
    list_filter = ('action', 'entity_type', 'performed_by')
    search_fields = ('action', 'entity_type')
