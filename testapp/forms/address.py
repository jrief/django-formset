from django.forms import fields, forms

from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.widgets import Button


class AddressForm(forms.Form):
    """
    Grouping fields using CSS
    """

    recipient = fields.CharField(
        label="Recipient",
        max_length=100,
    )
    postal_code = fields.CharField(
        label="Postal Code",
        max_length=8,
    )
    city = fields.CharField(
        label="City",
        max_length=50,
    )
    submit = Activator(
        label="Submit",
        widget=Button(
            action='disable -> submit -> reload !~ scrollToError',
            button_variant=ButtonVariant.PRIMARY,
            icon_path='formset/icons/send.svg',
        ),
    )
    reset = Activator(
        label="Reset to initial",
        widget=Button(
            action='reset',
            button_variant=ButtonVariant.WARNING,
            icon_path='formset/icons/reset.svg',
        ),
    )
