# -*- coding: utf-8 -*-


from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext, ugettext_lazy as _
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
    list_display = ('email', 'date_joined', 'first_name', 'last_name', 'is_active', 'is_admin', 'is_warehouse', 'is_accounting', 'locations',)
    list_filter = ('is_admin', 'is_warehouse', 'is_accounting',)
    fieldsets = (
        (None, {'fields': ('email', 'password',)}),
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

# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)


class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'created_on', 'company_name',)
    list_editable = ()
    list_filter = ()
    search_fields = ('company_name',)
admin.site.register(Client, ClientAdmin)


class ClientUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'client', 'title')
    list_editable = ()
    list_filter = ('client', 'user')
    search_fields = ('client__company_name', 'user__first_name', 'user__last_name', 'user__email')
admin.site.register(ClientUser, ClientUserAdmin)


class CustContactAdmin(admin.ModelAdmin):
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
    list_editable = ()
    list_filter = ()
    autocomplete_fields = ('client', 'customer_contact', 'contact_user',)
admin.site.register(Location, LocationAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(Product, ProductAdmin)


class ShipperAddressAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(ShipperAddress, ShipperAddressAdmin)


class ShipmentAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(Shipment, ShipmentAdmin)


class ReceivableAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(Receivable, ReceivableAdmin)


class TransactionAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(Transaction, TransactionAdmin)


class PalletAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(Pallet, PalletAdmin)


class PalletContentsAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(PalletContents, PalletContentsAdmin)


class ShipmentDocAdmin(admin.ModelAdmin):
    list_editable = ()
    list_filter = ()
admin.site.register(ShipmentDoc, ShipmentDocAdmin)

