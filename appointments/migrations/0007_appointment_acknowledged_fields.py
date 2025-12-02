# Generated migration for adding acknowledged fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0006_appointment_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='patient_acknowledged',
            field=models.BooleanField(default=False, help_text='Patient marked completed appointment as done'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='doctor_acknowledged',
            field=models.BooleanField(default=False, help_text='Doctor marked completed appointment as done'),
        ),
    ]
