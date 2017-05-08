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
    is_accounting = models.BooleanField(default=False)
    is_warehouse = models.BooleanField(default=False)
    phone_number = PhoneNumberField(blank=True)
    notes = models.TextField(blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_deleted = models.DateTimeField(null=True, blank=True)

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
    email = models.EmailField(max_length=192, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, db_column='createdon')
    is_preferred = models.BooleanField(default=False, db_column='preferred')
    is_active = models.BooleanField(default=True, db_column='enabled')
    notes = models.TextField(blank=True)
    company_name = models.CharField(max_length=150, blank=True, db_column='coname')
    has_warehousing = models.BooleanField(default=True, db_column='warehousing')
    parent = models.ForeignKey('Client', null=True, blank=True, db_column='parent')

    def unicode(self):
        return (self.company_name)

    class Meta:
        db_table = 'Customers'


# Future model to map client contacts (formerly CustContacts) to clients, in a many-to-many relationship.
class ClientUser(models.Model):
    client = models.ForeignKey('Client', null=True)
    user = models.ForeignKey('User')
    title = models.CharField(max_length=100, blank=True)
    last_login_client = models.DateTimeField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    def unicode(self):
        return ('{0} {1}'.format(self.first_name, self.last_name))


class CustContact(models.Model):
    id = models.AutoField(primary_key=True, db_column='custcontactid')
    client = models.ForeignKey('Client', db_column='customerid')
    email = models.EmailField(max_length=192, blank=True)
    password = models.CharField(max_length=255, blank=True, db_column='pass')
    first_name = models.CharField(max_length=150, blank=True, db_column='fname')
    last_name = models.CharField(max_length=150, blank=True, db_column='lname')
    title = models.CharField(max_length=100, blank=True)
    phone_number = PhoneNumberField(max_length=30, blank=True, db_column='tel')
    phone_extension = models.CharField(max_length=5, blank=True, db_column='telext')
    fax = PhoneNumberField(max_length=30, blank=True)
    mobile_number = PhoneNumberField(max_length=30, blank=True, db_column='mobile')
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_column='enabled')
    last_login = models.DateTimeField(null=True, blank=True, db_column='lastlogin')
    notes = models.TextField(blank=True)

    def unicode(self):
        return ('{0} {1}'.format(self.first_name, self.last_name))

    class Meta:
        db_table = 'CustContacts'


class AdminUser(models.Model):
    ACCESS_LEVEL_CHOICES = (
        (1, 'Admin'),
        (2, 'Customer Management'),
        (3, 'Product Management'),
        (4, 'Marketing Only'),
        (5, 'BBS Only'),
    )

    TWO_FACTOR_CHOICES = (
        (1, 'OTP auth'),
        (2, 'SMS auth'),
    )

    id = models.AutoField(primary_key=True, db_column='adminid')
    username = models.CharField(max_length=100, blank=True, db_column='user')
    password = models.CharField(max_length=255, blank=True, db_column='pass')
    created_by = models.ForeignKey('AdminUser', null=True, blank=True, db_column='createdbyadminid')
    is_authority = models.BooleanField(default=False, db_column='authority')
    is_founder = models.BooleanField(default=False, db_column='founder')
    full_name = models.CharField(max_length=150, blank=True, db_column='fullname')
    email = models.EmailField(max_length=192, blank=True)
    about = models.TextField(blank=True)
    access_level = models.IntegerField(choices=ACCESS_LEVEL_CHOICES, db_column='acclev')
    is_sleeping = models.BooleanField(default=False, db_column='sleeping')
    date_created = models.DateTimeField(auto_now_add=True)
    pic_first_name = models.CharField(max_length=255, blank=True, db_column='picfname')
    mobile_number = PhoneNumberField(max_length=30, blank=True, db_column='cell')
    two_factor_type = models.IntegerField(choices=TWO_FACTOR_CHOICES, db_column='twofac')
    is_active = models.BooleanField(default=True, db_column='enable')

    def unicode(self):
        return ('{0}'.format(self.username))

    class Meta:
        db_table = 'admin'


class WarehouseUser(models.Model):
    ROLE_CHOICES = (
        ('accounting', 'Accounting'),
        ('warehouse', 'Warehouse'),
    )

    id = models.AutoField(primary_key=True, db_column='wuserid')
    username = models.CharField(max_length=100, blank=True, db_column='user')
    password = models.CharField(max_length=255, blank=True, db_column='pass')
    created_by = models.ForeignKey('AdminUser', null=True, blank=True, db_column='createdbyadminid')
    full_name = models.CharField(max_length=150, blank=True, db_column='fullname')
    email = models.EmailField(max_length=192, blank=True)
    about = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
    last_login = models.DateTimeField(null=True, db_column='lastlogin')
    login_count = models.IntegerField(default=0, db_column='logintimes')
    is_active = models.BooleanField(default=True, db_column='enable')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    def unicode(self):
        return ('{0}'.format(self.username))

    class Meta:
        db_table = 'wuser'


class Location(models.Model):
    id = models.AutoField(primary_key=True, db_column='locationid')
    client = models.ForeignKey('Client', db_column='customerid')
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


class Product(models.Model):
    PREPAY_CHOICES = (
        (1, 'INVQ'),
        (2, 'Prepaid'),
    )

    id = models.AutoField(primary_key=True, db_column='productid')
    client = models.ForeignKey('Client', db_column='customerid')
    product_id = models.CharField(max_length=10, db_column='PRID')
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
    packing = models.IntegerField(null=True, blank=True)
    cases_inventory = models.IntegerField(null=True, blank=True, db_column='remain')
    units_inventory = models.IntegerField(null=True, blank=True, db_column='totalq')
    gross_weight = models.IntegerField(null=True, blank=True, db_column='GW')
    is_domestic = models.BooleanField(default=False, db_column='prodtype')
    name = models.CharField(max_length=255, blank=True, db_column='pname'),
    client_product_id = models.CharField(max_length=24, blank=True, db_column='ctag')
    contracted_quantity = models.BigIntegerField(null=True, blank=True, db_column='contqty')
    is_active = models.BooleanField(default=True, db_column='active')
    length = models.CharField(max_length=10, blank=True)
    width = models.CharField(max_length=10, blank=True)
    height = models.CharField(max_length=10, blank=True)
    item_number = models.CharField(max_length=12, blank=True, db_column='itemnum')
    location = models.ForeignKey('Location', null=True, blank=True, db_column='locationid')
    account_prepay_type = models.IntegerField(choices=PREPAY_CHOICES, db_column='account')

    def unicode(self):
        return (self.name)

    class Meta:
        db_table = 'Products'


class ShipperAddress(models.Model):
    name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    def unicode(self):
        return (self.name)


class Shipment(models.Model):
    STATUS_CHOICES = (
        (0, 'Pending'),
        (1, 'Ready to Ship'),
        (2, 'Shipped'),
    )

    ACCOUNTING_STATUS_CHOICES = (
        (0, 'INVQ'),
        (1, 'Pending'),
        (2, 'Submitted'),
    )

    id = models.AutoField(primary_key=True, db_column='shipmentid')
    client = models.ForeignKey('Client', db_column='customerid')
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
    date_shipped = models.DateTimeField(null=True, blank=True, db_column='shippedon')
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    carrier = models.CharField(max_length=50, blank=True)
    tracking = models.CharField(max_length=50, blank=True)
    ship_by = models.IntegerField(null=True, blank=True, db_column='shipby')
    purchase_order = models.CharField(max_length=50, blank=True, db_column='PO')
    shipment_order = models.CharField(max_length=50, blank=True, db_column='SO')
    location = models.ForeignKey('Location', null=True, blank=True, db_column='locationid')
    third_party = models.CharField(max_length=50, blank=True, db_column='3rdparty')
    third_party_address = models.TextField(blank=True, db_column='3rdpartyaddress')
    third_party_phone_number = PhoneNumberField(blank=True, db_column='3rdpartyphone')
    third_party_per = models.CharField(max_length=30, blank=True, db_column='3rdpartyper')
    third_party_received = models.CharField(max_length=16, blank=True, db_column='3rdpartyrecvd')
    third_party_charges_advanced = models.CharField(max_length=16, blank=True, db_column='3rdpartychgadvanced')
    pro_number = models.CharField(max_length=50, blank=True, db_column='pro')
    purchase_order_number = models.CharField(max_length=50, blank=True, db_column='loadnum')
    shipper_instructions = models.TextField(blank=True, db_column='shipperinstructions')
    consignee_instructions = models.TextField(blank=True, db_column='consigneeinstructions')
    shipper_address = models.ForeignKey('ShipperAddress', null=True, blank=True, db_column='shipperaddress')
    inside_delivery = models.BooleanField(default=False, db_column='insidedelivery')
    liftgate_required = models.BooleanField(default=False, db_column='liftgate')
    appointment_required = models.BooleanField(default=False, db_column='appointment')
    sort_segregation =models.BooleanField(default=False, db_column='sortseg')
    shipment_class = models.CharField(max_length=50, blank=True, db_column='class')
    pallet_count = models.IntegerField(null=True, blank=True, db_column='numpallets')
    accounting_status = models.IntegerField(choices=ACCOUNTING_STATUS_CHOICES, db_column='acctstatus')
    invoice_number = models.IntegerField(null=True, blank=True, db_column='invoice')

    def unicode(self):
        return (self.id)

    class Meta:
        db_table = 'Shipments'


class Receivable(models.Model):
    id = models.AutoField(primary_key=True, db_column='receivableid')
    client = models.ForeignKey('Client', db_column='customerid')
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
    purchase_order = models.CharField(max_length=50, blank=True, db_column='PO')
    shipment_order = models.CharField(max_length=50, blank=True, db_column='SO')
    product = models.ForeignKey('Product', db_column='productid')
    cases = models.IntegerField(null=True, blank=True)

    def unicode(self):
        return (self.id)

    class Meta:
        db_table = 'Receivables'


class Transaction(models.Model):
    id = models.AutoField(primary_key=True, db_column='transactionid')
    date_created = models.DateTimeField(auto_now_add=True, db_column='stamp')
    product = models.ForeignKey('Product', db_column='productid')
    quantity = models.IntegerField(null=True, blank=True, db_column='qty')
    quantity_remaining = models.BigIntegerField(null=True, blank=True, db_column='qtyremain')
    is_outbound = models.BooleanField(default=False, db_column='direction')
    shipment = models.ForeignKey('Shipment', null=True, blank=True, db_column='shipmentid')
    client = models.ForeignKey('Client', db_column='customerid')
    cases = models.IntegerField(null=True, blank=True)
    shipment_order = models.CharField(max_length=50, blank=True, db_column='SO')
    receivable = models.ForeignKey('Receivable', null=True, blank=True, db_column='receivableid')
    transfer_client = models.ForeignKey('Client', null=True, blank=True, db_column='transfercustomerid', related_name='transfers')
    transfer_product = models.ForeignKey('Product', null=True, blank=True, db_column='transferproductid', related_name='transfers')

    def unicode(self):
        return (self.id)

    class Meta:
        db_table = 'Transactions'

