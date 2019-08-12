from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from django.forms.models import inlineformset_factory

from localflavor.us.forms import USStateField, USZipCodeField
from localflavor.us.us_states import STATE_CHOICES

from ims.models import User, Client, CustContact, ClientUser, Location, Product, Receivable, Transaction, ShipmentDoc, Shipment, Pallet, ReturnedProduct
from ims import utils

import logging
logger = logging.getLogger(__name__)


ENABLED_CHOICES = (
    (True, 'Enabled'),
    (False, 'Disabled'),
)

WAREHOUSING_CHOICES = (
    (True, 'Warehousing required'),
    (False, 'No warehousing required'),
)

VIEW_ORDER_HISTORY_CHOICES = (
    (True, 'Can view order history'),
    (False, 'Cannot view order history'),
)

DOMESTIC_CHOICES = (
    (False, 'Import (12-14 wks)'),
    (True, 'Domestic (6-8 wks)'),
)


class ClientCreateForm(forms.ModelForm):

    class Meta:
        model = Client
        fields = ['company_name',]


class ClientForm(forms.ModelForm):
    company_name = forms.CharField(label='Customer name', widget=forms.TextInput(attrs={'placeholder': 'Customer name'}))
    primary_contact = forms.ModelChoiceField(required=False, queryset=None, empty_label='(Select primary contact)')
    parent = forms.TypedChoiceField(required=False, empty_value=None)
    is_active = forms.ChoiceField(choices=ENABLED_CHOICES)
    has_warehousing = forms.ChoiceField(choices=WAREHOUSING_CHOICES)
    notes = forms.CharField(label='Notes', required=False, widget=forms.Textarea(attrs={'placeholder': 'Notes', 'class': 'smalltext', 'id': 'id_client_notes'}))

    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        all_clients = [(None, 'Subsidiary of...'), (None, '(None)')]
        for parent_client in utils.tree_to_list(Client.objects.filter(is_active=True).order_by('company_name'), sort_by='company_name'):
            indent = '&nbsp;&nbsp;&nbsp;&nbsp;'.join(['' for i in range(parent_client['depth'])])
            parent_client['indent'] = indent
#            all_clients.append(parent_client)
            choice_string = mark_safe('{0}{1}'.format(parent_client['indent'], parent_client['obj'].company_name))
            all_clients.append((parent_client['obj'].id, choice_string))
        self.fields['parent'].choices = all_clients
        all_contacts = CustContact.objects.filter(client=self.instance, is_active=True)
        self.fields['primary_contact'].queryset = all_contacts
        self.fields['primary_contact'].initial = all_contacts.filter(is_primary=True).first()

    def clean_parent(self):
        data = self.cleaned_data.get('parent')
        logger.warning(data)
        if data == None:
            return None
        return Client.objects.get(pk=data)

    class Meta:
        model = Client
        fields = ['company_name', 'is_active', 'has_warehousing', 'parent', 'notes']


class CustContactForm(forms.ModelForm):
    first_name = forms.CharField(label='First name', widget=forms.TextInput(attrs={'placeholder': 'First'}))
    last_name = forms.CharField(label='Last name', widget=forms.TextInput(attrs={'placeholder': 'Last'}))
    title = forms.CharField(label='Title', required=False, widget=forms.TextInput(attrs={'placeholder': 'Title'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'value': '********'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    phone_number = forms.CharField(label='Phone number', required=False, max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Phone'}))
    phone_extension = forms.CharField(label='Phone extension', required=False, max_length=5, widget=forms.TextInput(attrs={'placeholder': 'Ext'}))
    mobile_number = forms.CharField(label='Mobile number', required=False, max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Mobile'}))
    fax_number = forms.CharField(label='Fax number', required=False, max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Fax'}))
    notes = forms.CharField(label='Notes', required=False, widget=forms.Textarea(attrs={'placeholder': 'Notes', 'class': 'smalltext', 'id': 'id_contact_notes'}))

    def __init__(self, *args, **kwargs):
        super(CustContactForm, self).__init__(*args, **kwargs)
#        if self.instance:
#            self.fields['first_name'].widget.attrs['value'] = self.instance.user.first_name
#            self.fields['last_name'].widget.attrs['value'] = self.instance.user.last_name
#            self.fields['email'].widget.attrs['value'] = self.instance.user.email

        if self.instance.id == None:
            self.fields['password'].widget.attrs['value'] = ''
#            for field in self.fields:
#                try:
#                    self.fields[field].widget.attrs['class'] += ' new'
#                except KeyError:
#                    self.fields[field].widget.attrs['class'] = 'new'

#    def clean_password(self):
#        logger.warning(self.initial)
#        logger.warning(self.changed_data)
#        logger.warning(self.instance.password)
#        # Regardless of what the user provides, return the initial value.
#        # This is done here, rather than on the field, because the
#        # field does not have access to the initial value
#        return self.initial["password"]

    class Meta:
#        model = CustContact
        model = ClientUser
#        fields = ['client', 'first_name', 'last_name', 'password', 'title', 'email', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']
        fields = ['client', 'title']

#ClientUserFormSet = inlineformset_factory(User, ClientUser, extra=0, fields=('title',))


class UserForm(forms.ModelForm):
    first_name = forms.CharField(label='First name', widget=forms.TextInput(attrs={'placeholder': 'First'}))
    last_name = forms.CharField(label='Last name', widget=forms.TextInput(attrs={'placeholder': 'Last'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'value': '********'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    phone_number = forms.CharField(label='Phone number', required=False, max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Phone'}))
    phone_extension = forms.CharField(label='Phone extension', required=False, max_length=5, widget=forms.TextInput(attrs={'placeholder': 'Ext'}))
    mobile_number = forms.CharField(label='Mobile number', required=False, max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Mobile'}))
    fax_number = forms.CharField(label='Fax number', required=False, max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Fax'}))
    notes = forms.CharField(label='Notes', required=False, widget=forms.Textarea(attrs={'placeholder': 'Notes', 'class': 'smalltext', 'id': 'id_contact_notes'}))

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        logger.info(self.instance)
        self.fields['email'].widget.attrs['value'] = self.instance.email
        if self.instance.id == None:
            self.fields['password'].widget.attrs['value'] = ''
#            for field in self.fields:
#                try:
#                    self.fields[field].widget.attrs['class'] += ' new'
#                except KeyError:
#                    self.fields[field].widget.attrs['class'] = 'new'

    class Meta:
        model = User
#        fields = ['first_name', 'last_name', 'password', 'email', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']
        fields = ['first_name', 'last_name', 'password', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']


class UserCreateForm(UserForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']


class ClientUserForm(forms.ModelForm):
    title = forms.CharField(label='Title', required=False, widget=forms.TextInput(attrs={'placeholder': 'Title'}))
    view_order_history = forms.ChoiceField(choices=VIEW_ORDER_HISTORY_CHOICES)

    class Meta:
        model = ClientUser
        fields = ['client', 'title', 'view_order_history']


class LocationForm(forms.ModelForm):
    STATE_CHOICES_BLANK = list(STATE_CHOICES)
    STATE_CHOICES_BLANK.insert(0, ('', '(Select state)'))

    name = forms.CharField(label='Name', widget=forms.TextInput(attrs={'placeholder': 'Location name'}))
    state = USStateField(required=False, widget=forms.Select(choices=STATE_CHOICES_BLANK))
    zip = USZipCodeField(required=False, label='ZIP', widget=forms.TextInput(attrs={'placeholder': 'ZIP'}))

#    def __init__(self, *args, **kwargs):
#        super(LocationForm, self).__init__(*args, **kwargs)
#        if self.instance.id == None:
#            for field in self.fields:
#                try:
#                    self.fields[field].widget.attrs['class'] += ' new'
#                except KeyError:
#                    self.fields[field].widget.attrs['class'] = 'new'

    class Meta:
        model = Location
        fields = ['client', 'name', 'contact_user', 'address', 'address_2', 'city', 'state', 'zip', 'receiving_hours', 'notes']


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['contracted_quantity'].required = False
        if self.instance.contracted_quantity_units:
            self.initial['contracted_quantity'] = self.instance.contracted_quantity_units
        if self.instance.unit_price:
            self.initial['unit_price'] = '{:0.4f}'.format(self.instance.unit_price)
        if self.instance.gross_weight:
            self.initial['gross_weight'] = '{:0.1f}'.format(self.instance.gross_weight)

    def clean_contracted_quantity(self):
        if not self.cleaned_data.get('packing') or not self.cleaned_data.get('contracted_quantity'):
            return 0
        return self.cleaned_data.get('contracted_quantity') / self.cleaned_data.get('packing')

    def clean_location(self):
        return self.instance.location

    class Meta:
        model = Product
        fields = [
            'client',
            'item_number',
            'client_tag',
            'name',
            'packing',
            'cases_inventory',
#            'units_inventory',
            'account_prepay_type',
            'contracted_quantity',
            'unit_price',
            'gross_weight',
            'length',
            'width',
            'height',
            'is_domestic',
            'location',
        ]
        widgets = {
            'account_prepay_type': forms.Select(attrs={'style': 'display: block;'}),
            'contracted_quantity': forms.NumberInput(attrs={'style': 'width: 100px;'}),
            'unit_price': forms.NumberInput(attrs={'style': 'width: 65px;', 'min': 0, 'step': '0.0001', 'onchange': 'this.value = parseFloat(this.value).toFixed(4);'}),
            'gross_weight': forms.NumberInput(attrs={'style': 'width: 50px;'}),
            'length': forms.NumberInput(attrs={'style': 'width: 50px;'}),
            'width': forms.NumberInput(attrs={'style': 'width: 50px;'}),
            'height': forms.NumberInput(attrs={'style': 'width: 50px;'}),
            'is_domestic': forms.Select(choices=DOMESTIC_CHOICES, attrs={'style': 'display: block;'}),
        }


class ReceivableForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReceivableForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Receivable
        fields = [
            'client',
            'product',
            'purchase_order',
            'shipment_order',
            'cases',
            'date_received',
        ]
        widgets = {
            'purchase_order': forms.TextInput(attrs={'id': 'id_purchase_order_incoming', 'style': 'width: 100px;'}),
            'shipment_order': forms.TextInput(attrs={'id': 'id_shipment_order_incoming', 'style': 'width: 100px;'}),
            'cases': forms.NumberInput(attrs={'id': 'id_cases_incoming', 'style': 'width: 100px;'}),
            'date_received': forms.DateInput(attrs={'style': 'width: 100px;'}),
        }
        initial = {
        }


class ReceivableConfirmForm(forms.ModelForm):

    def clean_cases(self):
        if self.cleaned_data['cases'] > self.instance.cases:
            raise forms.ValidationError('More cases entered than expected.', code='more_than_expected')
        return self.cleaned_data['cases']

    class Meta:
        model = Receivable
        fields = ['cases', 'purchase_order', 'shipment_order']


class ReturnedProductForm(forms.ModelForm):
    class Meta:
        model = ReturnedProduct
        fields = ['cases_undamaged', 'cases_damaged', 'location', 'date_returned',]


class ShipmentDocForm(forms.ModelForm):
    class Meta:
        model = ShipmentDoc
        fields = ['shipment', 'file']


class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = [
            'shipper_address',
            'carrier',
            'pro_number',
            'purchase_order_number',
            'third_party',
            'shipment_class',
            'pallet_count',
            'date_shipped',
            'shipper_instructions',
            'consignee_instructions',
            'inside_delivery',
            'liftgate_required',
            'appointment_required',
            'sort_segregation',
        ]
        widgets = {
            'shipper_address': forms.Select(attrs={'style': 'margin: 10px 0px;'}),
            'date_shipped': forms.DateInput(format='%m/%d/%Y'),
        }


class PalletForm(forms.ModelForm):
    class Meta:
        model = Pallet
        fields = ['shipment',]

