# Generated migration for adding is_read field to AppointmentMessage

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0004_appointmentmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmentmessage',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]
