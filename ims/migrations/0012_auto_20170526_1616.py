# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-26 16:16


import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0011_transaction_date_completed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receivable',
            name='cases',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
