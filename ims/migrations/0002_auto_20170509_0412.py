# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-09 04:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipmentdoc',
            name='uuid',
            field=models.CharField(blank=True, max_length=35),
        ),
    ]