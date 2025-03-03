from django.forms import fields

from formset.fieldset import Fieldset
from formset.forms import Form


class AddressFieldset(Fieldset):
    legend = "Address"

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
    # postal_code = fields.CharField(
    #     label="Postal Code",
    #     max_length=8,
    #     required=False,
    # )
    # city = fields.CharField(
    #     label="City",
    #     max_length=50,
    #     required=False,
    # )


class CustomerForm(Form):
    billing = CustomerFieldset(
        legend="Billing",
    )
    shipping = CustomerFieldset(
        legend="Shipping",
        hide_condition='use_billing_address',
    )
    use_billing_address = fields.BooleanField(
        label="Use Billing Address for Shipping",
        required=False,
    )
