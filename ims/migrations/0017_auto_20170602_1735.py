# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-02 17:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0016_shipmentdoc_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipmentdoc',
            name='uuid',
            field=models.CharField(blank=True, max_length=36),
        ),
    ]