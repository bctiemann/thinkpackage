# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils.translation import ugettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=191,
        unique=True,
    )
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_admin = models.BooleanField(default=False)
    phone_number = PhoneNumberField(blank=True)

    USERNAME_FIELD = 'email'

    objects = UserManager()

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    @property
    def is_superuser(self):
        return self.is_admin


class Client(models.Model):
    id = models.AutoField(primary_key=True, db_column='customerid')
    email = models.CharField(max_length=255, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, db_column='createdon')
    is_preferred = models.BooleanField(default=False, db_column='preferred')
    is_enabled = models.BooleanField(default=True, db_column='enabled')
    notes = models.TextField(blank=True)
    company_name = models.CharField(max_length=150, blank=True, db_column='coname')
    has_warehousing = models.BooleanField(default=True, db_column='warehousing')
    parent = models.ForeignKey('Client', null=True, blank=True)

    def unicode(self):
        return (self.company_name)

    class Meta:
        db_table = 'Customers'


"""
class Location(models.Model):
    id = models.AutoField(primary_key=True, db_column='locationid')
    customer = models.ForeignKey('Customer', db_column='customerid')
    name = models.CharField(max_length=255, blank=True)
    phone = PhoneNumberField(max_length=30, blank=True, db_column='tel')
    phone_extension = models.CharField(max_length=5, blank=True, db_column='telext')
    fax = PhoneNumberField(max_length=30, blank=True)
    address = models.CharField(max_length=150, blank=True, db_column='addr')
    address_2 = models.CharField(max_length=150, blank=True, db_column='addr2')
    city = models.CharField(max_length=150, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=2, blank=True)
    non_us_state = models.CharField(max_length=150, blank=True, db_column='ostate')
    customer_contact = models.ForeignKey('CustContact', db_column='custcontactid')
    notes = models.TextField(blank=True)
    receiving_hours = models.CharField(max_length=100, blank=True, db_column='recvhours')

    def unicode(self):
        return (self.name)

    class Meta:
        db_table = 'Locations'
"""
