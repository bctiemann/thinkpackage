# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-07 14:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=191, unique=True, verbose_name='email address')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('is_admin', models.BooleanField(default=False)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(db_column='customerid', primary_key=True, serialize=False)),
                ('email', models.CharField(blank=True, max_length=255)),
                ('created_on', models.DateTimeField(auto_now_add=True, db_column='createdon')),
                ('is_preferred', models.BooleanField(db_column='preferred', default=False)),
                ('is_enabled', models.BooleanField(db_column='enabled', default=True)),
                ('notes', models.TextField(blank=True)),
                ('company_name', models.CharField(blank=True, db_column='coname', max_length=150)),
                ('has_warehousing', models.BooleanField(db_column='warehousing', default=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ims.Client')),
            ],
            options={
                'db_table': 'Customers',
            },
        ),
    ]
