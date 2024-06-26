# Generated by Django 2.2.9 on 2020-02-23 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0064_auto_20200223_2149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=1, default=0, max_digits=6, max_length=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='length',
            field=models.DecimalField(blank=True, decimal_places=1, default=0, max_digits=6, max_length=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='width',
            field=models.DecimalField(blank=True, decimal_places=1, default=0, max_digits=6, max_length=10),
            preserve_default=False,
        ),
    ]
