# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-11-01 19:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0052_asynctask_result_content_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asynctask',
            name='result_url',
        ),
    ]
