# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-09 11:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0032_shipment_delivery_charge'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('log_message', models.TextField(blank=True, null=True)),
                ('admin_user', models.ForeignKey(blank=True, db_column='adminid', null=True, on_delete=django.db.models.deletion.CASCADE, to='ims.AdminUser')),
                ('client', models.ForeignKey(blank=True, db_column='customerid', null=True, on_delete=django.db.models.deletion.CASCADE, to='ims.Client')),
                ('product', models.ForeignKey(blank=True, db_column='productid', null=True, on_delete=django.db.models.deletion.CASCADE, to='ims.Product')),
                ('warehouse_user', models.ForeignKey(blank=True, db_column='wuserid', null=True, on_delete=django.db.models.deletion.CASCADE, to='ims.WarehouseUser')),
            ],
        ),
    ]