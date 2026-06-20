from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0006_chatmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='address',
            field=models.CharField(max_length=200),
        ),
        migrations.AddField(
            model_name='appointment',
            name='ai_assigned_doctor',
            field=models.BooleanField(default=False),
        ),
    ]
