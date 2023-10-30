from django.forms import fields, forms

from formset.validators import phone_number_validator
from formset.widgets import PhoneNumberInput


class PhoneForm(forms.Form):
    """
    How to use the PhoneNumberInput widget.
    """
    phone_number = fields.CharField(
        label="Phone Number",
        validators=[phone_number_validator],
        widget=PhoneNumberInput,
    )

    mobile_number = fields.CharField(
        label="Mobile Number",
        initial='+43 664 1234567',
        validators=[phone_number_validator],
        widget=PhoneNumberInput(attrs={'default-country-code': 'at', 'mobile-only': True}),
    )
