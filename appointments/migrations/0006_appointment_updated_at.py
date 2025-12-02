# Generated migration for adding updated_at field to Appointment

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0005_appointmentmessage_is_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
