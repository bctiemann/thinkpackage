# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-07 19:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0005_auto_20170507_1922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custcontact',
            name='client',
            field=models.ForeignKey(db_column='customerid', on_delete=django.db.models.deletion.CASCADE, to='ims.Client'),
        ),
    ]
