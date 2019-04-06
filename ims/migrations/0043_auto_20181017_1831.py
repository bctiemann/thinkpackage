# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-17 18:31


import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0042_auto_20181012_2315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receivable',
            name='cases',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(1)]),
            preserve_default=False,
        ),
    ]
