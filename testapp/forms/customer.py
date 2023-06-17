from django.forms import fields, forms

from formset.fieldset import Fieldset
from formset.collection import FormCollection


class CustomerForm(Fieldset):
    legend = "Customer"
    hide_condition = 'register.no_customer'

    name = fields.CharField(
        label="Recipient",
        max_length=100,
    )

    address = fields.CharField(
        label="Address",
        max_length=100,
    )

    phone_number = fields.RegexField(
        r'^\+?[ 0-9.\-]{4,25}$',
        label="Phone Number",
        error_messages={'invalid': "Phone number have 4-25 digits and may start with '+'."},
        required=False,
    )


class RegisterForm(forms.Form):
    no_customer = fields.BooleanField(
        label="I'm not a customer",
        required=False,
    )


class CustomerCollection(FormCollection):
    customer = CustomerForm()

    register = RegisterForm()
