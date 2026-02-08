from .models import ActivityLog


def log_activity(action, entity_type, entity_id, user=None, note=None):
    ActivityLog.objects.create(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        performed_by=user,
        note=note
    )
