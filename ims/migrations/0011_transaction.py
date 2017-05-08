# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-08 00:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0010_receivable'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(db_column='transactionid', primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, db_column='stamp')),
                ('quantity', models.IntegerField(blank=True, db_column='qty', null=True)),
                ('quantity_remaining', models.BigIntegerField(blank=True, db_column='qtyremain', null=True)),
                ('is_outbound', models.BooleanField(db_column='direction', default=False)),
                ('cases', models.IntegerField(blank=True, null=True)),
                ('shipment_order', models.CharField(blank=True, db_column='SO', max_length=50)),
                ('client', models.ForeignKey(db_column='customerid', on_delete=django.db.models.deletion.CASCADE, to='ims.Client')),
                ('product', models.ForeignKey(db_column='productid', on_delete=django.db.models.deletion.CASCADE, to='ims.Product')),
                ('receivable', models.ForeignKey(blank=True, db_column='receivableid', null=True, on_delete=django.db.models.deletion.CASCADE, to='ims.Receivable')),
                ('shipment', models.ForeignKey(blank=True, db_column='shipmentid', null=True, on_delete=django.db.models.deletion.CASCADE, to='ims.Shipment')),
                ('transfer_client', models.ForeignKey(db_column='transfercustomerid', on_delete=django.db.models.deletion.CASCADE, related_name='transfers', to='ims.Client')),
                ('transfer_product', models.ForeignKey(db_column='transferproductid', on_delete=django.db.models.deletion.CASCADE, related_name='transfers', to='ims.Product')),
            ],
            options={
                'db_table': 'Transactions',
            },
        ),
    ]
