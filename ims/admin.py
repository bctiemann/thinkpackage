# -*- coding: utf-8 -*-


from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.admin.models import LogEntry
from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from ims.models import *

import logging
logger = logging.getLogger(__name__)


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField(
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user's password, but you can change the password using "
            "<a href=\"../password/\">this form</a>."
        ),
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'is_active', 'is_admin',)

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = (
        'email',
        'last_login',
        'first_name',
        'last_name',
        'is_active',
        'is_admin',
        'is_warehouse',
        'is_accounting',
        'two_factor_enabled',
        'locations',
        'clients',
    )
    list_filter = ('is_admin', 'is_warehouse', 'is_accounting',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'date_password_changed', 'date_password_prompt_dismissed',)}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'notes',)}),
        ('Permissions', {'fields': ('is_active', 'is_admin', 'is_accounting', 'is_warehouse', 'date_deleted',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    def two_factor_enabled(self, instance):
        return instance.two_factor_enabled
    two_factor_enabled.boolean = True

# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)


class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'created_on', 'company_name',)
    list_editable = ()
    list_filter = ()
    search_fields = ('id', 'company_name',)
    autocomplete_fields = ('parent',)
admin.site.register(Client, ClientAdmin)


class ClientUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'client', 'title')
    list_editable = ()
    list_filter = ('client', 'user')
    search_fields = ('client__company_name', 'user__first_name', 'user__last_name', 'user__email')
    autocomplete_fields = ('client', 'user',)
admin.site.register(ClientUser, ClientUserAdmin)


class CustContactAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'client', 'title', 'phone_number', 'is_active',)
    list_editable = ()
    list_filter = ()
    search_fields = ('first_name', 'last_name', 'email',)
    formfield_overrides = {
        PhoneNumberField: {'widget': PhoneNumberPrefixWidget(initial='US'), }
    }
admin.site.register(CustContact, CustContactAdmin)


class AdminUserAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(AdminUser, AdminUserAdmin)


class WarehouseUserAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(WarehouseUser, WarehouseUserAdmin)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'client', 'is_active',)
    list_editable = ()
    list_filter = ('client',)
    autocomplete_fields = ('client', 'customer_contact', 'contact_user',)
    search_fields = ('id', 'name', 'client__company_name',)
admin.site.register(Location, LocationAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('item_number', 'name', 'client', )
    list_editable = ()
    list_filter = ()
    search_fields = ('item_number', 'name', 'client__company_name',)
    autocomplete_fields = ('client', 'location',)
admin.site.register(Product, ProductAdmin)


class ShipperAddressAdmin(admin.ModelAdmin):
    list_display = ('name', 'address',)
    list_editable = ()
    list_filter = ()
admin.site.register(ShipperAddress, ShipperAddressAdmin)


class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'user', 'date_created', 'status', 'accounting_status',)
    list_editable = ()
    list_filter = ()
    search_fields = ('id', 'client__company_name',)
    autocomplete_fields = ('client', 'user', 'location',)
admin.site.register(Shipment, ShipmentAdmin)


class ReceivableAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'product', 'cases', 'purchase_order', 'shipment_order', 'date_created', 'date_received',)
    list_editable = ()
    list_filter = ()
    search_fields = ('id', 'client__company_name',)
    autocomplete_fields = ('client', 'product',)
admin.site.register(Receivable, ReceivableAdmin)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'product', 'date_created', 'date_completed', 'shipment', 'cases', 'is_outbound', 'receivable',)
    list_editable = ()
    list_filter = ()
    autocomplete_fields = ('client', 'product', 'shipment', 'receivable', 'transfer_product', 'transfer_client',)
admin.site.register(Transaction, TransactionAdmin)


class PalletAdmin(admin.ModelAdmin):
    list_display = ('pallet_id', 'client', 'date_created',)
    list_editable = ()
    list_filter = ()
    search_fields = ('pallet_id', 'client__company_name',)
    autocomplete_fields = ('shipment', 'client',)
admin.site.register(Pallet, PalletAdmin)


class PalletContentsAdmin(admin.ModelAdmin):
    list_display = ('product', 'pallet',)
    list_editable = ()
    list_filter = ()
    autocomplete_fields = ('pallet', 'product',)
admin.site.register(PalletContents, PalletContentsAdmin)


class ShipmentDocAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'file', 'shipment', 'date_created',)
    list_editable = ()
    list_filter = ()
    search_fields = ('uuid', 'basename', 'shipment__client__company_name',)
    autocomplete_fields = ('shipment',)
admin.site.register(ShipmentDoc, ShipmentDocAdmin)


class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'user', 'log_message', 'client', 'product', 'app',)
    list_editable = ()
    list_filter = ()
    autocomplete_fields = ('product', 'client', 'user',)
admin.site.register(ActionLog, ActionLogAdmin)


class BulkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'filename', 'date_ordered', 'date_imported', 'shipment',)
    list_editable = ()
    list_filter = ()
    search_fields = ('id', 'client', 'filename',)
    autocomplete_fields = ('client', 'location', 'shipment',)
admin.site.register(BulkOrder, BulkOrderAdmin)


class BulkOrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'bulk_order', 'item_number', 'product_name', 'quantity',)
    list_editable = ()
    list_filter = ()
    autocomplete_fields = ('bulk_order',)
admin.site.register(BulkOrderItem, BulkOrderItemAdmin)


class AsyncTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_created', 'name', 'percent_complete', 'is_complete', 'has_failed',)
    list_editable = ()
    list_filter = ()
admin.site.register(AsyncTask, AsyncTaskAdmin)


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', '__str__')
    readonly_fields = ('content_type',
        'user',
        'action_time',
        'object_id',
        'object_repr',
        'action_flag',
        'change_message'
    )

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(LogEntry, LogEntryAdmin)
admin.site.site_header = f'{settings.COMPANY_NAME} administration'
