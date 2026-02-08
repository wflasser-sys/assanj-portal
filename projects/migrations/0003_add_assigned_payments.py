# Generated manual migration to add assigned_payments JSONField
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_alter_project_project_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='assigned_payments',
            field=models.JSONField(blank=True, null=True, default=dict),
        ),
    ]
