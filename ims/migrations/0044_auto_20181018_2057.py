# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-18 20:57


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0043_auto_20181017_1831'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='quantity_remaining',
        ),
        migrations.AddField(
            model_name='transaction',
            name='cases_remaining',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
