# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-01 23:37


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0014_user_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='login_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
