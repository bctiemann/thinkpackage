# Generated by Django 3.0.3 on 2020-03-11 22:33

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0069_auto_20200310_0917'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='date_password_changed',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
    ]
