# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-08 21:42


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0018_client_ancestors'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='client_product_id',
            new_name='client_tag',
        ),
    ]
