from django import forms

from ims.models import CustContact

import logging
logger = logging.getLogger(__name__)


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

