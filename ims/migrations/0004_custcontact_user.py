# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-15 23:15
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0003_auto_20170514_2307'),
    ]

    operations = [
        migrations.AddField(
            model_name='custcontact',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]