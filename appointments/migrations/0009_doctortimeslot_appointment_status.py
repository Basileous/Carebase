from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # Replace '0008_...' with the actual last migration name in your project
        ('appointments', '0008_patient_profile_complete_alter_appointment_doctor'),
    ]

    operations = [
        # Add status field to Appointment
        migrations.AddField(
            model_name='appointment',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
                default='pending',
                max_length=10,
            ),
        ),
        # Create DoctorTimeSlot model
        migrations.CreateModel(
            name='DoctorTimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(
                    choices=[
                        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
                        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'),
                        ('Sunday', 'Sunday'),
                    ],
                    max_length=10,
                )),
                ('time_slot', models.TimeField()),
                ('doctor', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='time_slots',
                    to='appointments.doctor',
                )),
            ],
            options={
                'ordering': ['day', 'time_slot'],
                'unique_together': {('doctor', 'day', 'time_slot')},
            },
        ),
    ]
