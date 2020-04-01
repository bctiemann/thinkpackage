# -*- coding: utf-8 -*-


from django.conf import settings
from django.urls import reverse
from django.db import models
from django.db.models import F, FloatField, Sum
from django.db.models.functions import Lower, Coalesce, Trunc
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.module_loading import import_string
from django.core.validators import MaxValueValidator, MinValueValidator

from django_countries.fields import CountryField
from jsonfield import JSONField
from localflavor.us.us_states import STATE_CHOICES
from two_factor.utils import default_device

from ims import utils

import os
import uuid
import random
import qrcode
import qrcode.image.svg
import datetime

import logging
logger = logging.getLogger(__name__)


KG_TO_LB_MULTIPLIER = 2.20462
CM_TO_IN_MULTIPLIER = 0.393701


def get_report_path(instance, filename):
    return 'reports/{0}'.format(filename)

def get_document_path(instance, filename):
    return 'shipment_docs/{0}/{1}'.format(str(instance.id).upper(), filename)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super(SoftDeleteManager, self).get_queryset().filter(is_active=True)
    def all_with_deleted(self):
        return super(SoftDeleteManager, self).get_queryset()
    def deleted_set(self):
        return super(SoftDeleteManager, self).get_queryset().filter(is_active=False)


class LowercaseEmailField(models.EmailField):
    """
    Override EmailField to convert emails to lowercase before saving.
    """
    def to_python(self, value):
        """
        Convert email to lowercase.
        """
        value = super(LowercaseEmailField, self).to_python(value)
        # Value can be None so check that it's a string before lowercasing.
        if isinstance(value, str):
            return value.lower()
        return value


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
    email = LowercaseEmailField(
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
    phone_number = models.CharField(max_length=30, blank=True)
    phone_extension = models.CharField(max_length=5, blank=True)
    fax_number = models.CharField(max_length=30, blank=True)
    mobile_number = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_deleted = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL)
    last_login = models.DateTimeField(null=True, blank=True)
    login_count = models.IntegerField(null=True, blank=True)
    date_password_changed = models.DateTimeField(default=timezone.now, blank=True)
    date_password_prompt_dismissed = models.DateTimeField(default=timezone.now, blank=True)

    USERNAME_FIELD = 'email'

    objects = UserManager()

    @property
    def full_name(self):
        return '{0} {1}'.format(self.first_name, self.last_name)

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def set_password(self, raw_password):
        self.date_password_changed = timezone.now()
        super().set_password(raw_password)

    @property
    def child_clients(self):
        if self.is_admin or self.email == settings.CLIENTACCESS_EMAIL:
            return utils.tree_to_list(Client.objects.filter(is_active=True), sort_by='company_name_lower')

        # List of clients this user is associated with, along with depth for rendering with indents in a select menu
        child_clients = []
        client_users = ClientUser.objects.filter(user=self, client__is_active=True).order_by('client__company_name')
        for cu in client_users:
            children_of_other = utils.list_at_node(utils.tree_to_list(Client.objects.filter(is_active=True), sort_by='company_name'), cu.client)
            for child in children_of_other:
                if not child in child_clients:
                    child_clients.append(child)
        return child_clients

    # Don't use authorized_clients; it doesn't take all hierarchical children/ancestors into account
    @property
    def authorized_clients(self):
        return [client_user.client for client_user in ClientUser.objects.filter(user=self, client__is_active=True).order_by('client__company_name')]

    @property
    def clients(self):
        return ', '.join([client.company_name for client in self.authorized_clients])

    @property
    def locations(self):
        return ', '.join(['{0} ({1})'.format(location.client.company_name, location.name) for location in Location.objects.filter(contact_user__user=self)])

    def is_authorized_for_client(self, client):
        if self.is_admin:
            return True
        if not client:
            return False
        return ClientUser.objects.filter(user=self, client__is_active=True, client__id__in=client.ancestors).exists()

    @property
    def is_authorized_for_docs(self):
        return self.is_admin or self.is_accounting or self.is_warehouse

    @property
    def is_staff(self):
        # Is the user a member of staff?
        # Simplest possible answer: All admins are staff
        return self.is_admin

    @property
    def is_superuser(self):
        return self.is_admin

    @property
    def two_factor_enabled(self):
        return bool(default_device(self))

    @property
    def password_expired(self):
        return (timezone.now() - self.date_password_changed).days >= settings.PASSWORD_EXPIRE_DAYS

    @property
    def password_prompt_should_reappear(self):
        return (timezone.now() - self.date_password_prompt_dismissed).days >= settings.PASSWORD_PROMPT_REAPPEAR_DAYS

    @property
    def prompt_password_change(self):
        return False
        # return self.password_expired and self.password_prompt_should_reappear

    def set_password_to_expired(self):
        self.date_password_changed = timezone.now() - datetime.timedelta(days=settings.PASSWORD_EXPIRE_DAYS)
        self.save()


class ClientManager(models.Manager):

    def get_queryset(self):
        return super(ClientManager, self).get_queryset().order_by(Lower('company_name'))


class Client(models.Model):
    id = models.AutoField(primary_key=True, db_column='customerid')
    email = models.EmailField(max_length=192, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, db_column='createdon')
    is_preferred = models.BooleanField(default=False, db_column='preferred')
    is_active = models.BooleanField(default=True, db_column='enabled')
    notes = models.TextField(blank=True)
    company_name = models.CharField(max_length=150, blank=True, db_column='coname')
    has_warehousing = models.BooleanField(default=True, db_column='warehousing')
    parent = models.ForeignKey('Client', null=True, blank=True, db_column='parent', on_delete=models.SET_NULL)
    ancestors = JSONField(null=True, blank=True)

    objects = ClientManager()

    @property
    def children(self):
        # Get list of clients at or below the selected client in the hierarchy
        return utils.list_at_node(utils.tree_to_list(Client.objects.filter(is_active=True), sort_by='company_name'), self)

    @property
    def company_name_lower(self):
        return self.company_name.lower()

    @property
    def company_name_clean(self):
        return self.company_name.replace(',', '')

    @property
    def contacts(self):
        return self.clientuser_set.exclude(user__email=settings.CLIENTACCESS_EMAIL).order_by('-is_primary', 'user__first_name')

    def __str__(self):
        return (self.company_name)

    def get_absolute_url(self):
        return reverse('mgmt:profile', kwargs={'client_id': self.id})

    def get_ancestors(self):
        new_ancestors = []
        if self.parent:
            new_ancestors.append(self.parent)
            new_ancestors += self.parent.get_ancestors()
        return new_ancestors

    def save(self, *args, **kwargs):
        started_with_id = self.id
        if not self.created_on:
            self.created_on = timezone.now()
        super(Client, self).save(*args, **kwargs)

        try:
            clientaccess_user = User.objects.get(email=settings.CLIENTACCESS_EMAIL)
            client_user, created = ClientUser.objects.get_or_create(user=clientaccess_user, client=self)
        except User.DoesNotExist:
            pass

        # If this instance had been previously created, we can populate the ancestors directly. However, if this
        # is the first time creating the instance, we don't have the id, so we rely on the post_save signal
        # executing populate_client_ancestors() in ims/apps.py.
        if started_with_id:
            self.ancestors = [self.id] + [a.id for a in self.get_ancestors()]
            super(Client, self).save(*args, **kwargs)

    class Meta:
        db_table = 'Customers'
        ordering = ('company_name',)


# New-style model to map client contacts (formerly CustContacts) to clients, in a many-to-many relationship.
class ClientUser(models.Model):
    client = models.ForeignKey('Client', null=True, on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True)
    last_login_client = models.DateTimeField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    view_order_history = models.BooleanField(default=True)

    def __str__(self):
        return ('{0} {1}'.format(self.user.first_name, self.user.last_name))

    def get_absolute_url(self):
        return reverse('mgmt:contact-update', kwargs={'custcontact_id': self.pk})


# Legacy model assigning unique users to clients; replaced by ClientUser mapping
class CustContact(models.Model):
    id = models.AutoField(primary_key=True, db_column='custcontactid')
    client = models.ForeignKey('Client', db_column='customerid', on_delete=models.CASCADE)
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)
    email = models.EmailField(max_length=192, blank=True)
    password = models.CharField(max_length=255, blank=True, db_column='pass')
    first_name = models.CharField(max_length=150, blank=True, db_column='fname')
    last_name = models.CharField(max_length=150, blank=True, db_column='lname')
    title = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=30, blank=True, db_column='tel')
    phone_extension = models.CharField(max_length=5, blank=True, db_column='telext')
    fax_number = models.CharField(max_length=30, blank=True, db_column='fax')
    mobile_number = models.CharField(max_length=30, blank=True, db_column='mobile')
    is_primary = models.BooleanField(default=False, db_column='isprimary')
    is_active = models.BooleanField(default=True, db_column='enabled')
    last_login = models.DateTimeField(null=True, blank=True, db_column='lastlogin')
    notes = models.TextField(blank=True)

    def __str__(self):
        return ('{0} {1}'.format(self.first_name, self.last_name))

    def get_absolute_url(self):
        return reverse('mgmt:profile', kwargs={'client_id': self.client.id})

    class Meta:
        db_table = 'CustContacts'
        ordering = ['-is_primary', 'last_name']


class AdminUser(models.Model):

    class AccessLevel(models.IntegerChoices):
        ADMIN = 1, _('Admin')
        CUSTOMER_MANAGEMENT = 2, _('Customer Management')
        PRODUCT_MANAGEMENT = 3, _('Product Management')
        MARKETING = 4, _('Marketing Only')
        BBS = 5, _('BBS Only')

    class TwoFactorType(models.IntegerChoices):
        OTP = 1, _('OTP auth')
        SMS = 2, _('SMS auth')

    id = models.AutoField(primary_key=True, db_column='adminid')
    username = models.CharField(max_length=100, blank=True, db_column='user')
    password = models.CharField(max_length=255, blank=True, db_column='pass')
    created_by = models.ForeignKey('AdminUser', null=True, blank=True, db_column='createdbyadminid', on_delete=models.SET_NULL)
    is_authority = models.BooleanField(default=False, db_column='authority')
    is_founder = models.BooleanField(default=False, db_column='founder')
    full_name = models.CharField(max_length=150, blank=True, db_column='fullname')
    email = models.EmailField(max_length=192, blank=True)
    about = models.TextField(blank=True)
    access_level = models.IntegerField(choices=AccessLevel.choices, db_column='acclev')
    is_sleeping = models.BooleanField(default=False, db_column='sleeping')
    date_created = models.DateTimeField(auto_now_add=True, db_column='stamp')
    pic_first_name = models.CharField(max_length=255, blank=True, db_column='picfname')
    mobile_number = models.CharField(max_length=30, blank=True, db_column='cell')
    two_factor_type = models.IntegerField(choices=TwoFactorType.choices, db_column='twofac')
    is_active = models.BooleanField(default=True, db_column='enable')

    def __str__(self):
        return ('{0}'.format(self.username))

    class Meta:
        db_table = 'admin'


class WarehouseUser(models.Model):

    class Role(models.TextChoices):
        ACCOUNTING = 'accounting', _('Accounting')
        WAREHOUSE = 'warehouse', _('Warehouse')

    id = models.AutoField(primary_key=True, db_column='wuserid')
    username = models.CharField(max_length=100, blank=True, db_column='user')
    password = models.CharField(max_length=255, blank=True, db_column='pass')
    created_by = models.ForeignKey('AdminUser', null=True, blank=True, db_column='createdbyadminid', on_delete=models.SET_NULL)
    full_name = models.CharField(max_length=150, blank=True, db_column='fullname')
    email = models.EmailField(max_length=192, blank=True)
    about = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
    last_login = models.DateTimeField(null=True, db_column='lastlogin')
    login_count = models.IntegerField(default=0, db_column='logintimes')
    is_active = models.BooleanField(default=True, db_column='enable')
    role = models.CharField(max_length=30, choices=Role.choices)

    def __str__(self):
        return ('{0}'.format(self.username))

    class Meta:
        db_table = 'wuser'


class Location(models.Model):
    id = models.AutoField(primary_key=True, db_column='locationid')
    client = models.ForeignKey('Client', db_column='customerid', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=30, blank=True, db_column='tel')
    phone_extension = models.CharField(max_length=5, blank=True, db_column='telext')
    fax_number = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=150, blank=True, db_column='addr')
    address_2 = models.CharField(max_length=150, blank=True, db_column='addr2')
    city = models.CharField(max_length=150, blank=True)
    state = models.CharField(choices=STATE_CHOICES, max_length=2, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    # country = models.CharField(max_length=2, blank=True)
    country = CountryField(blank=True, blank_label='(Select country)')
    non_us_state = models.CharField(max_length=150, blank=True, db_column='ostate')
    customer_contact = models.ForeignKey('CustContact', null=True, blank=True, db_column='custcontactid', on_delete=models.SET_NULL)
    contact_user = models.ForeignKey('ClientUser', null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    receiving_hours = models.CharField(max_length=100, blank=True, db_column='recvhours')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return (self.name)

    def get_absolute_url(self):
        return reverse('mgmt:location-update', kwargs={'location_id': self.pk})

    class Meta:
        db_table = 'Locations'
        ordering = ['name']


class Product(models.Model):

    class AccountingPrepayType(models.IntegerChoices):
        INVQ = 1, _('INVQ')
        PREPAID = 2, _('Prepaid')

    id = models.AutoField(primary_key=True, db_column='productid')
    client = models.ForeignKey('Client', db_column='customerid', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=10, db_column='PRID', db_index=True)
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
    packing = models.IntegerField(null=True, blank=True)
    cases_inventory = models.IntegerField(null=True, blank=True, db_column='remain')
    units_inventory_old = models.IntegerField(null=True, blank=True, db_column='totalq')
    unit_price = models.DecimalField(max_digits=10, decimal_places=5, blank=True, db_column='unitprice')
    gross_weight = models.DecimalField(max_digits=7, decimal_places=2, blank=True, db_column='GW')
    is_domestic = models.BooleanField(default=False, db_column='prodtype')
    name = models.CharField(max_length=255, blank=True, db_column='pname')
    client_tag = models.CharField(max_length=24, blank=True, db_column='ctag')
    contracted_quantity = models.BigIntegerField(null=True, blank=True, db_column='contqty')
    is_active = models.BooleanField(default=True, db_column='active')
    is_deleted = models.BooleanField(default=False)
    length = models.DecimalField(max_digits=6, decimal_places=1, max_length=10, blank=True)
    width = models.DecimalField(max_digits=6, decimal_places=1, max_length=10, blank=True)
    height = models.DecimalField(max_digits=6, decimal_places=1, max_length=10, blank=True)
    item_number = models.CharField(max_length=12, blank=True, db_column='itemnum')
    location = models.ForeignKey('Location', null=True, blank=True, db_column='locationid', on_delete=models.SET_NULL)
    accounting_prepay_type = models.IntegerField(choices=AccountingPrepayType.choices, null=True, blank=True, db_column='account')

    @property
    def units_inventory(self):
        return self.cases_inventory * self.packing

    @property
    def is_low(self):
        if not self.contracted_quantity:
            return False
        return float(self.cases_inventory) / float(self.contracted_quantity) < 0.5

    @property
    def pending_receivables(self):
        return Transaction.objects.filter(product=self, is_outbound=False, cases__isnull=True)

    @property
    def cases_unshipped(self):
        return Shipment.objects.filter(transaction__product=self, status__lt=2).aggregate(cases_unshipped=Sum('transaction__cases'))['cases_unshipped'] or 0

    @property
    def cases_available(self):
        return self.cases_inventory - self.cases_unshipped

    @property
    def units_available(self):
        return (self.cases_inventory - self.cases_unshipped) * self.packing

    @property
    def contracted_quantity_units(self):
        if not self.contracted_quantity or not self.packing:
            return None
        return self.contracted_quantity * self.packing

    @property
    def case_price(self):
        return self.unit_price * self.packing

    @property
    def total_price(self):
        if not self.unit_price or not self.contracted_quantity or not self.packing:
            return None
        return self.unit_price * self.contracted_quantity * self.packing

    @property
    def gross_weight_imperial(self):
        if not self.gross_weight:
            return 0
        return float(self.gross_weight) * KG_TO_LB_MULTIPLIER

    @property
    def length_imperial(self):
        if not self.length:
            return 0
        return float(self.length) * CM_TO_IN_MULTIPLIER

    @property
    def width_imperial(self):
        if not self.width:
            return 0
        return float(self.width) * CM_TO_IN_MULTIPLIER

    @property
    def height_imperial(self):
        if not self.height:
            return 0
        return float(self.height) * CM_TO_IN_MULTIPLIER

    @property
    def cases_available(self):
        return self.cases_inventory - self.cases_unshipped

    @property
    def last_shipment(self):
        return self.transaction_set.filter(is_outbound=True).order_by('-date_created').first().shipment

    @property
    def last_transaction(self):
        return self.transaction_set.order_by('-date_created').first()

    @property
    def last_receivable(self):
        return self.receivable_set.order_by('-date_created').first()

    @property
    def item_number_force_string(self):
        return self.item_number
        # Unnecessary to append a tab because item_number being interpreted as an int in Excel is fine
        # return f'{self.item_number}\t'

    def __str__(self):
        return f'[{self.item_number}] {self.name}'

    def create_qrcode(self):
        img = self.get_qrcode(format='PNG')
        img.save('{0}/codes/products/{1}.png'.format(settings.MEDIA_ROOT, self.product_id))

    def get_qrcode(self, format='PNG'):
        if format == 'PNG':
            image_factory_string = 'qrcode.image.pil.PilImage'
        elif format == 'SVG':
            image_factory_string = 'qrcode.image.svg.SvgPathFillImage'
        image_factory = import_string(image_factory_string)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=44,
            border=1,
            image_factory=image_factory,
        )

        code = '1TP:{product_id}'.format(product_id=self.product_id)
        qr.add_data(code)
        qr.make(fit=True)
        return qr.make_image()

    def get_history(self, date_from):
        history = self.transaction_set.filter(date_created__gt=date_from)
        history = history.annotate(date_requested=Trunc(Coalesce('receivable__date_created', 'date_created'), 'day'))
        history = history.annotate(date_in_out=Trunc(Coalesce('shipment__date_shipped', 'date_created'), 'day'))
        history = history.order_by('-date_in_out', '-shipment__id')

        cases_balance_differential = self.cases_inventory
        for transaction in history:
            if not transaction.cases:
                continue
            transaction.cases_remaining_differential = cases_balance_differential
            transaction.units_remaining_differential = cases_balance_differential * self.packing
            if transaction.is_shipped or not transaction.is_outbound or transaction.is_transfer:
                if transaction.is_outbound:
                    cases_balance_differential += transaction.cases
                else:
                    cases_balance_differential -= transaction.cases

        return history

    def get_absolute_url(self):
        return reverse('mgmt:inventory', kwargs={'client_id': self.client.id})

    def save(self, *args, **kwargs):
        if not self.product_id:
            self.product_id = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(10))
        super(Product, self).save(*args, **kwargs)

    class Meta:
        db_table = 'Products'
        ordering = ['item_number']


class ShipperAddress(models.Model):
    name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return (self.name)


class Shipment(models.Model):

    class Status(models.IntegerChoices):
        PENDING = 0, _('Pending')
        READY = 1, _('Ready to Ship')
        SHIPPED = 2, _('Shipped')

    class AccountingStatus(models.IntegerChoices):
        INVQ = 0, _('INVQ')
        PENDING = 1, _('Pending')
        SUBMITTED = 2, _('Submitted')

    id = models.AutoField(primary_key=True, db_column='shipmentid')
    client = models.ForeignKey('Client', db_column='customerid', on_delete=models.CASCADE)
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
    date_shipped = models.DateTimeField(null=True, blank=True, db_column='shippedon')
    status = models.IntegerField(choices=Status.choices, default=0)
    carrier = models.CharField(max_length=50, blank=True, default='')
    tracking = models.CharField(max_length=50, blank=True, default='')
    ship_by = models.IntegerField(null=True, blank=True, db_column='shipby')
    purchase_order = models.CharField(max_length=50, blank=True, default='', db_column='PO')
    shipment_order = models.CharField(max_length=50, blank=True, default='', db_column='SO')
    location = models.ForeignKey('Location', null=True, blank=True, db_column='locationid', on_delete=models.SET_NULL)
    third_party = models.CharField(max_length=50, blank=True, default='', db_column='3rdparty')
    third_party_address = models.TextField(null=True, blank=True, db_column='3rdpartyaddress')
    third_party_phone_number = models.CharField(max_length=30, blank=True, default='', db_column='3rdpartyphone')
    third_party_per = models.CharField(max_length=30, blank=True, default='', db_column='3rdpartyper')
    third_party_received = models.CharField(max_length=16, blank=True, default='', db_column='3rdpartyrecvd')
    third_party_charges_advanced = models.CharField(max_length=16, blank=True, default='', db_column='3rdpartychgadvanced')
    pro_number = models.CharField(max_length=50, blank=True, default='', db_column='pro')
    purchase_order_number = models.CharField(max_length=50, blank=True, default='', db_column='loadnum')
    shipper_instructions = models.TextField(null=True, blank=True, db_column='shipperinstructions')
    consignee_instructions = models.TextField(null=True, blank=True, default='', db_column='consigneeinstructions')
    shipper_address = models.ForeignKey('ShipperAddress', null=True, blank=True, default=settings.DEFAULT_SHIPPER_ADDRESS, db_column='shipperaddress', on_delete=models.SET_NULL)
    inside_delivery = models.BooleanField(default=False, db_column='insidedelivery')
    liftgate_required = models.BooleanField(default=False, db_column='liftgate')
    appointment_required = models.BooleanField(default=False, db_column='appointment')
    sort_segregation = models.BooleanField(default=False, db_column='sortseg')
    shipment_class = models.CharField(max_length=50, blank=True, default='', db_column='class')
    pallet_count = models.IntegerField(null=True, blank=True, db_column='numpallets')
    accounting_status = models.IntegerField(choices=AccountingStatus.choices, default=0, db_column='acctstatus')
    invoice_number = models.IntegerField(null=True, blank=True, db_column='invoice')
    delivery_charge = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True, db_column='deliverycharge')

    @property
    def is_pending(self):
        return self.status in [self.Status.PENDING, self.Status.READY] and self.id != None

    @property
    def is_shipped(self):
        return self.status == self.Status.SHIPPED

    @property
    def total_pallets(self):
        return Pallet.objects.filter(shipment=self).distinct().count()

    @property
    def total_cases(self):
        total_cases = 0
        for transaction in self.transaction_set.all():
            total_cases += transaction.cases
        return total_cases

    @property
    def total_pieces(self):
        total_pieces = 0
        for transaction in self.transaction_set.all():
            total_pieces += transaction.cases * transaction.product.packing
        return total_pieces

    @property
    def total_price(self):
        total_price = 0
        for transaction in self.transaction_set.all():
            total_price += transaction.total_price
        return total_price

    @property
    def total_weight(self):
        total_weight = 0
        for transaction in self.transaction_set.all():
            total_weight += transaction.total_weight
        return total_weight

    @property
    def total_weight_imperial(self):
        total_weight_imperial = 0
        for transaction in self.transaction_set.all():
            total_weight_imperial += transaction.total_weight_imperial
        return total_weight_imperial

    def __str__(self):
        return ('{0}'.format(self.id))

    def get_absolute_url(self):
        return reverse('warehouse:shipment-details', kwargs={'shipment_id': self.id})

    class Meta:
        db_table = 'Shipments'


class Receivable(models.Model):
    id = models.AutoField(primary_key=True, db_column='receivableid')
    client = models.ForeignKey('Client', db_column='customerid', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')
    date_received = models.DateTimeField(null=True, blank=True)
    purchase_order = models.CharField(max_length=50, blank=True, db_column='PO')
    shipment_order = models.CharField(max_length=50, blank=True, db_column='SO')
    product = models.ForeignKey('Product', null=True, db_column='productid', on_delete=models.SET_NULL)
    cases = models.IntegerField(validators=[MinValueValidator(1)])
    returned_product = models.ForeignKey('ReturnedProduct', null=True, blank=True, db_column='returnid', on_delete=models.SET_NULL)

    @property
    def transaction(self):
        return self.transaction_set.first()

    def __str__(self):
        return ('{0}'.format(self.id))

    def get_absolute_url(self):
        return reverse('mgmt:inventory', kwargs={'client_id': self.client.id})

    class Meta:
        db_table = 'Receivables'


class Transaction(models.Model):
    id = models.AutoField(primary_key=True, db_column='transactionid')
    date_created = models.DateTimeField(auto_now_add=True, db_column='stamp')
    date_completed = models.DateTimeField(null=True, blank=True)
    product = models.ForeignKey('Product', db_column='productid', on_delete=models.CASCADE)
#    quantity = models.IntegerField(null=True, blank=True, db_column='qty')
#    quantity_remaining = models.BigIntegerField(null=True, blank=True, db_column='qtyremain')
    cases_remaining = models.BigIntegerField(null=True, blank=True)
    is_outbound = models.BooleanField(default=False, db_column='direction')
    shipment = models.ForeignKey('Shipment', null=True, blank=True, db_column='shipmentid', on_delete=models.CASCADE)
    client = models.ForeignKey('Client', db_column='customerid', on_delete=models.CASCADE)
    cases = models.IntegerField(null=True, blank=True)
    shipment_order = models.CharField(max_length=50, blank=True, db_column='SO')
    receivable = models.ForeignKey('Receivable', null=True, blank=True, db_column='receivableid', on_delete=models.CASCADE)
    transfer_client = models.ForeignKey('Client', null=True, blank=True, db_column='transfercustomerid', related_name='transfers', on_delete=models.SET_NULL)
    transfer_product = models.ForeignKey('Product', null=True, blank=True, db_column='transferproductid', related_name='transfers', on_delete=models.SET_NULL)
    is_scanned_to_pallet = models.BooleanField(default=False)

#    @property
#    def cases_remaining(self):
#        return int(float(self.quantity_remaining) / float(self.product.packing))

#    @property
#    def request_date(self):
#        if not self.shipment and not self.receivable:
#            return self.date_created.date()
#        elif not self.is_outbound:
#            return self.receivable.date_created.date()
#        return self.date_created.date()

#    @property
#    def in_out_date(self):
#        if not self.shipment and not self.receivable:
#            return self.date_created.date()
#        elif not self.is_outbound:
#            return self.date_created.date()
#        return self.shipment.date_shipped.date()

    @property
    def quantity_remaining(self):
        return self.units_remaining

    @property
    def units_remaining(self):
        return int(float(self.cases_remaining) * float(self.product.packing))

    @property
    def cases_received_split(self):
        if not self.receivable:
            return None
        if not self.receivable.cases or not self.cases:
            return None
        return (self.receivable.cases - self.cases) * -1

    @property
    def total_quantity(self):
        if not self.cases:
            return 0
        if not self.product.packing:
            return 0
        return self.cases * self.product.packing

    @property
    def total_price(self):
        return self.product.unit_price * self.product.packing * self.cases

    @property
    def total_weight(self):
        return self.cases * float(self.product.gross_weight)

    @property
    def total_weight_imperial(self):
        return self.cases * float(self.product.gross_weight_imperial)

    # Number of pallets dedicated to this product
    @property
    def total_pallets_for_product(self):
        dedicated_pallets = 0
        for pallet_share in PalletContents.objects.filter(pallet__shipment=self.shipment, product=self.product):
            if PalletContents.objects.filter(pallet=pallet_share.pallet).exclude(product=self.product).count() == 0:
                dedicated_pallets += 1
        return dedicated_pallets

    # Number of products sharing the pallet this product is on
    @property
    def total_pallet_shares(self):
        product_shares = 0
        for pallet_share in PalletContents.objects.filter(pallet__shipment=self.shipment, product=self.product):
            product_shares += PalletContents.objects.filter(pallet=pallet_share.pallet).count()
        return product_shares

    # Number of pallets, or Fraction of the current pallet, this product takes up
    @property
    def pallet_share(self):
        if self.total_pallet_shares == 1:
            return self.total_pallets_for_product
        return '1/{0}'.format(self.total_pallet_shares)

    @property
    def is_transfer(self):
        return self.transfer_client != None

    @property
    def is_return(self):
        return self.receivable and self.receivable.returned_product

    @property
    def is_shipped(self):
        if not self.shipment:
            return False
        return self.shipment.status == 2

    def get_absolute_url(self):
        return reverse('mgmt:inventory', kwargs={'client_id': self.client.id, 'product_id': self.product.id})

    def __str__(self):
        return ('{0}'.format(self.id))

    class Meta:
        db_table = 'Transactions'
        ordering = ['product__item_number']


class ReturnedProduct(models.Model):
    id = models.AutoField(primary_key=True, db_column='returnid')
    date_returned = models.DateTimeField(null=True, db_column='stamp')
    client = models.ForeignKey('Client', db_column='customerid', null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey('Product', db_column='productid', null=True, on_delete=models.SET_NULL)
    location = models.ForeignKey('Location', db_column='locationid', null=True, on_delete=models.SET_NULL)
    cases_damaged = models.IntegerField(null=True, blank=True, default=0)
    cases_undamaged = models.IntegerField(null=True, blank=True, default=0)
    date_reconciled = models.DateTimeField(null=True, blank=True, db_column='reconciled')

    def get_absolute_url(self):
        return reverse('mgmt:inventory', kwargs={'client_id': self.client.id, 'product_id': self.product.id})

    class Meta:
        db_table = 'Returns'


class Pallet(models.Model):
    id = models.AutoField(primary_key=True, db_column='palletid')
    pallet_id = models.CharField(max_length=10, db_column='PID', db_index=True)
    shipment = models.ForeignKey('Shipment', db_column='shipmentid', null=True, blank=True, on_delete=models.SET_NULL)
    client = models.ForeignKey('Client', db_column='customerid', null=True, blank=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, db_column='createdon')

    def create_qrcode(self):
        img = self.get_qrcode(format='PNG')
        img.save('{0}/codes/pallets/{1}.png'.format(settings.MEDIA_ROOT, self.pallet_id))

    def get_qrcode(self, format='PNG'):
        if format == 'PNG':
            image_factory_string = 'qrcode.image.pil.PilImage'
        elif format == 'SVG':
            image_factory_string = 'qrcode.image.svg.SvgPathFillImage'
        image_factory = import_string(image_factory_string)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=44,
            border=1,
            image_factory=image_factory,
        )
        try:
            purchase_order = self.shipment.purchase_order
        except AttributeError:
            purchase_order = ''

        contents = []
        for content in self.palletcontents_set.all():
            contents.append('{0}:{1}'.format(content.product.id, content.cases))

        code = '1TP:{pallet_id};{content};{purchase_order}'.format(pallet_id=self.pallet_id, content=','.join(contents), purchase_order=purchase_order)
        qr.add_data(code)
        qr.make(fit=True)
        return qr.make_image()

    @property
    def gross_weight(self):
        total_weight = 0
        for content in self.palletcontents_set.all():
            total_weight += content.gross_weight
        return total_weight

    @property
    def gross_weight_imperial(self):
        return float(self.gross_weight) * KG_TO_LB_MULTIPLIER

    def __str__(self):
        return ('{0}'.format(self.id))

    def save(self, *args, **kwargs):
        if not self.pallet_id:
            self.pallet_id = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(10))
#        self.create_qrcode()
        super(Pallet, self).save(*args, **kwargs)

    class Meta:
        db_table = 'Pallets'


class PalletContents(models.Model):
    id = models.AutoField(primary_key=True, db_column='onpalletid')
    pallet = models.ForeignKey('Pallet', db_column='palletid', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', db_column='productid', on_delete=models.CASCADE)
    cases = models.IntegerField(db_column='qty')

    @property
    def gross_weight(self):
        return self.product.gross_weight * self.cases

    def __str__(self):
        return ('{0}'.format(self.id))

    class Meta:
        db_table = 'OnPallet'
        verbose_name_plural = 'pallet contents'


class ShipmentDoc(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey('Shipment', null=True, db_column='shipmentid', on_delete=models.SET_NULL)
    file = models.FileField(max_length=255, upload_to=get_document_path, null=True, blank=True)
    basename = models.CharField(max_length=255, blank=True)
    ext = models.CharField(max_length=10, blank=True)
    size = models.IntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=32, blank=True, db_column='mimetype')
    date_created = models.DateTimeField(auto_now_add=True, db_column='stamp')

    def get_absolute_url(self):
        return reverse('shipment-doc', kwargs={'doc_id': self.id})

    def __str__(self):
        return ('{0}.{1}'.format(self.basename, self.ext))

    class Meta:
        db_table = 'ShipmentDocs'


class ActionLog(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, db_column='stamp')
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL)
    admin_user = models.ForeignKey('AdminUser', null=True, blank=True, db_column='adminid', on_delete=models.SET_NULL)
    warehouse_user = models.ForeignKey('WarehouseUser', null=True, blank=True, db_column='wuserid', on_delete=models.SET_NULL)
    client = models.ForeignKey('Client', null=True, blank=True, db_column='customerid', on_delete=models.SET_NULL)
    product = models.ForeignKey('Product', null=True, blank=True, db_column='productid', on_delete=models.SET_NULL)
    log_message = models.TextField(null=True, blank=True)
    app = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        ordering = ('-date_created',)


class BulkOrder(models.Model):
    id = models.AutoField(primary_key=True, db_column='bulkorderid')
    client = models.ForeignKey('Client', null=True, db_column='customerid', on_delete=models.SET_NULL)
    filename = models.CharField(max_length=50, blank=True, default='')
    date_ordered = models.DateTimeField(null=True, blank=True, db_column='stamp')
    date_imported = models.DateTimeField(auto_now_add=True, db_column='imported')
    location = models.ForeignKey('Location', null=True, db_column='locationid', on_delete=models.SET_NULL)
    purchase_order = models.CharField(max_length=40, blank=True, default='', db_column='PO')
    date_delivery = models.DateTimeField(null=True, blank=True, db_column='deliverydate')
    account_number = models.CharField(max_length=32, blank=True, default='', db_column='accountnum')
    message = models.CharField(max_length=50, blank=True, default='')
    location_address_1 = models.CharField(max_length=200, blank=True, default='', db_column='locaddress1')
    location_address_2 = models.CharField(max_length=200, blank=True, default='', db_column='locaddress2')
    location_city = models.CharField(max_length=160, blank=True, default='', db_column='loccity')
    location_state = models.CharField(max_length=12, blank=True, default='', db_column='locstate')
    location_zip = models.CharField(max_length=40, blank=True, default='', db_column='loczip')
    shipment = models.ForeignKey('Shipment', null=True, blank=True, db_column='shipmentid', on_delete=models.SET_NULL)

    class Meta:
        db_table = 'BulkOrders'


class BulkOrderItem(models.Model):

    class SplitFlag(models.TextChoices):
        Y = 'Y', _('Yes')
        N = 'N', _('No')

    id = models.AutoField(primary_key=True, db_column='bulkorderitemid')
    bulk_order = models.ForeignKey('BulkOrder', null=True, db_column='bulkorderid', on_delete=models.SET_NULL)
    item_number = models.CharField(max_length=40, blank=True, default='', db_column='itemnum')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='quantity')
    package_type = models.CharField(max_length=20, blank=True, default='', db_column='pkgtype')
    split_flag = models.CharField(choices=SplitFlag.choices, max_length=1, blank=True, default='', db_column='splitflag')
    product_name = models.TextField(null=True, blank=True, db_column='pname')
    bid_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, db_column='bidprice')

    class Meta:
        db_table = 'BulkOrderItems'


class AsyncTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, blank=True, default='')
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL)
    is_complete = models.BooleanField(default=False)
    has_failed = models.BooleanField(default=False)
    percent_complete = models.FloatField(default=0)
#    result_url = models.CharField(max_length=255, blank=True, default='')
    result_file = models.FileField(max_length=255, upload_to=get_report_path, null=True, blank=True)
    result_content_type = models.CharField(max_length=255, blank=True, default='')

    @property
    def result_url(self):
        return reverse('mgmt:async-task-result', kwargs={'async_task_id': self.id})

    @property
    def result_filename(self):
        if not self.result_file:
            return ''
        return os.path.basename(self.result_file.name)

    @property
    def result_basename(self):
        if not self.result_file:
            return ''
        return '.'.join(self.result_filename.split('.')[:-1])

    @property
    def result_extension(self):
        if not self.result_file:
            return ''
        return self.result_filename.split('.')[-1].lower()

    class Meta:
        ordering = ('-date_created',)