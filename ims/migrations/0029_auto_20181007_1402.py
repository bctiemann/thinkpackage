# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-07 14:02


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0028_bulkorder_shipment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='carrier',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='consignee_instructions',
            field=models.TextField(blank=True, db_column='consigneeinstructions', default=''),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='pro_number',
            field=models.CharField(blank=True, db_column='pro', default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='purchase_order',
            field=models.CharField(blank=True, db_column='PO', default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='purchase_order_number',
            field=models.CharField(blank=True, db_column='loadnum', default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='shipment_class',
            field=models.CharField(blank=True, db_column='class', default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='shipment_order',
            field=models.CharField(blank=True, db_column='SO', default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='shipper_instructions',
            field=models.TextField(blank=True, db_column='shipperinstructions', default=''),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='third_party',
            field=models.CharField(blank=True, db_column='3rdparty', default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='third_party_address',
            field=models.TextField(blank=True, db_column='3rdpartyaddress', default=''),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='third_party_charges_advanced',
            field=models.CharField(blank=True, db_column='3rdpartychgadvanced', default='', max_length=16),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='third_party_per',
            field=models.CharField(blank=True, db_column='3rdpartyper', default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='third_party_phone_number',
            field=models.CharField(blank=True, db_column='3rdpartyphone', default='', max_length=30),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='third_party_received',
            field=models.CharField(blank=True, db_column='3rdpartyrecvd', default='', max_length=16),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='tracking',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
