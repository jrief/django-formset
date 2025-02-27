from django.forms import fields

from formset.fieldset import Fieldset
from formset.form import Form


class AddressFieldset(Fieldset):
    postal_code = fields.CharField(
        label="Postal Code",
        max_length=8,
        required=False,
    )
    city = fields.CharField(
        label="City",
        max_length=50,
        required=False,
    )


class CustomerFieldset(Fieldset):
    recipient = fields.CharField(
        label="Recipient",
        max_length=100,
        required=False,
    )
    address = AddressFieldset()


class CustomerForm(Form):
    billing_address = CustomerFieldset(
        legend="Billing Address",
    )
    shipping_address = CustomerFieldset(
        legend="Shipping Address",
        hide_condition='use_billing_address',
    )
    use_billing_address = fields.BooleanField(
        label="Use Billing Address for Shipping",
        required=False,
    )
