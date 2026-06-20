from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0009_doctortimeslot_appointment_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notif_type', models.CharField(
                    choices=[
                        ('rescheduled', 'Appointment Rescheduled'),
                        ('cancelled', 'Appointment Cancelled'),
                        ('accepted', 'Appointment Accepted'),
                        ('rejected', 'Appointment Rejected'),
                    ],
                    max_length=20,
                )),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to='appointments.patient',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
