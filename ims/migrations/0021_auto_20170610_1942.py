# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-10 19:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0020_shipment_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='accounting_status',
            field=models.IntegerField(choices=[(0, 'INVQ'), (1, 'Pending'), (2, 'Submitted')], db_column='acctstatus', default=0),
        ),
    ]