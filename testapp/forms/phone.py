from django.forms import fields, forms

from formset.widgets import PhoneNumberInput


class PhoneForm(forms.Form):
    """
    How to use the PhoneNumberInput widget.
    """
    phone_number = fields.CharField(
        label="Phone Number",
        widget=PhoneNumberInput,
    )
