# Generated by Django 3.0.7 on 2020-12-20 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0082_auto_20200402_1211'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={},
        ),
        migrations.AddField(
            model_name='shipment',
            name='purchase_order_deadline',
            field=models.DateField(blank=True, null=True),
        ),
    ]
