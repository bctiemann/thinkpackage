from django import forms
from django.utils.safestring import mark_safe

from localflavor.us.forms import USStateField, USZipCodeField
from localflavor.us.us_states import STATE_CHOICES

from ims.models import Client, CustContact, Location
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


class ClientForm(forms.ModelForm):
    company_name = forms.CharField(label='Customer name', widget=forms.TextInput(attrs={'placeholder': 'Customer name', 'style': 'width: 260px; margin: 7px;'}))
    primary_contact = forms.ModelChoiceField(required=False, queryset=None, empty_label='(Select primary contact)')
    parent = forms.TypedChoiceField(required=False, empty_value=None)
    is_active = forms.ChoiceField(choices=ENABLED_CHOICES)
    has_warehousing = forms.ChoiceField(choices=WAREHOUSING_CHOICES)
    notes = forms.CharField(label='Notes', required=False, widget=forms.Textarea(attrs={'placeholder': 'Notes', 'class': 'smalltext', 'style': 'width: 469px;'}))

    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        all_clients = [(None, 'Subsidiary of...'), (None, '(None)')]
        for parent_client in utils.tree_to_list(Client.objects.filter(is_active=True).order_by('company_name'), sort_by='company_name'):
            indent = '&nbsp;&nbsp;&nbsp;&nbsp;'.join(['' for i in xrange(parent_client['depth'])])
            parent_client['indent'] = indent
#            all_clients.append(parent_client)
            choice_string = mark_safe('{0}{1}'.format(parent_client['indent'], parent_client['obj'].company_name))
            all_clients.append((parent_client['obj'].id, choice_string))
        logger.warning(all_clients)
        self.fields['parent'].choices = all_clients
        all_contacts = CustContact.objects.filter(client=self.instance)
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
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'value': '********', 'style': 'width: 469px;'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Email', 'style': 'width: 469px;'}))

#    def clean_password(self):
#        logger.warning(self.initial)
#        logger.warning(self.changed_data)
#        logger.warning(self.instance.password)
#        # Regardless of what the user provides, return the initial value.
#        # This is done here, rather than on the field, because the
#        # field does not have access to the initial value
#        return self.initial["password"]

    class Meta:
        model = CustContact
        fields = ['first_name', 'last_name', 'password', 'title', 'email', 'phone_number', 'phone_extension', 'mobile_number', 'fax_number', 'notes']


class LocationForm(forms.ModelForm):
    STATE_CHOICES_BLANK = list(STATE_CHOICES)
    STATE_CHOICES_BLANK.insert(0, ('', '(Select state)'))

    state = USStateField(widget=forms.Select(choices=STATE_CHOICES_BLANK, attrs={'style': 'width: 110px'}))
    zip = USZipCodeField(label='ZIP', widget=forms.TextInput(attrs={'placeholder': 'ZIP', 'style': 'width: 97px;'}))

    class Meta:
        model = Location
        fields = ['name', 'customer_contact', 'address', 'address_2', 'city', 'state', 'zip', 'receiving_hours', 'notes']
