# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-07 20:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('ims', '0005_auto_20170507_2012'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminUser',
            fields=[
                ('id', models.AutoField(db_column='adminid', primary_key=True, serialize=False)),
                ('username', models.CharField(blank=True, db_column='user', max_length=100)),
                ('password', models.CharField(blank=True, db_column='pass', max_length=255)),
                ('is_authority', models.BooleanField(db_column='authority', default=False)),
                ('is_founder', models.BooleanField(db_column='founder', default=False)),
                ('full_name', models.CharField(blank=True, db_column='fullname', max_length=150)),
                ('email', models.EmailField(blank=True, max_length=192)),
                ('about', models.TextField(blank=True)),
                ('access_level', models.IntegerField(choices=[(1, 'Admin'), (2, 'Customer Management'), (3, 'Product Management'), (4, 'Marketing Only'), (5, 'BBS Only')], db_column='acclev')),
                ('is_sleeping', models.BooleanField(db_column='sleeping', default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('pic_first_name', models.CharField(blank=True, db_column='picfname', max_length=255)),
                ('mobile_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, db_column='cell', max_length=30)),
                ('two_factor_type', models.IntegerField(choices=[(1, 'OTP auth'), (2, 'SMS auth')], db_column='twofac')),
                ('is_active', models.BooleanField(db_column='enable', default=True)),
                ('created_by', models.ForeignKey(blank=True, db_column='createdbyadminid', null=True, on_delete=django.db.models.deletion.CASCADE, to='ims.AdminUser')),
            ],
            options={
                'db_table': 'admin',
            },
        ),
        migrations.AlterField(
            model_name='custcontact',
            name='email',
            field=models.EmailField(blank=True, max_length=192),
        ),
    ]
