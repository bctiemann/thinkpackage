# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-10-09 18:49


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0036_auto_20181009_1357'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actionlog',
            options={'ordering': ('-date_created',)},
        ),
        migrations.AddField(
            model_name='actionlog',
            name='app',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
