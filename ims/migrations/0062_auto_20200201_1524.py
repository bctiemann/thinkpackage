# Generated by Django 2.2.9 on 2020-02-01 15:24

from django.db import migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0061_auto_20191122_0854'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='country',
            field=django_countries.fields.CountryField(max_length=2),
        ),
    ]