# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-18 22:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0044_auto_20181018_2057'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='is_scanned_to_pallet',
            field=models.BooleanField(default=False),
        ),
    ]
