from django.forms.fields import CharField, RegexField
from django.forms.forms import Form
from django.forms.widgets import TextInput

from formset.formfields.activator import Activator
from formset.renderers import ButtonVariant
from formset.stepper import StepperCollection
from formset.widgets import Button


class ContactForm(Form):
    step_label = "Contact"
    induce_activate = 'shipping.previous:active'

    first_name = CharField()
    last_name = CharField()
    next = Activator(
        label="Next",
        widget=Button(
            action='submitPartial -> activate("apply") !~ scrollToError',
            button_variant=ButtonVariant.SECONDARY,
            icon_path='formset/icons/chevron-right.svg',
            attrs={'class': 'float-end'},
        )
    )


class ShippingForm(Form):
    step_label = "Shipping"
    induce_activate = 'contact.next:active || payment.previous:active'

    street = CharField(
        label="Street",
    )
    postal_code = CharField(
        label="Postal Code",
    )
    city = CharField(
        label="City",
    )
    previous = Activator(
        label="Previous",
        widget=Button(
            action='activate("apply")',
            button_variant=ButtonVariant.SECONDARY,
            icon_path='formset/icons/chevron-left.svg',
            icon_left=True,
        )
    )
    next = Activator(
        label="Next",
        widget=Button(
            action='submitPartial -> activate("apply") !~ scrollToError',
            button_variant=ButtonVariant.SECONDARY,
            icon_path='formset/icons/chevron-right.svg',
            attrs={'class': 'float-end'},
        )
    )


class PaymentForm(Form):
    step_label = "Payment"
    induce_activate = 'shipping.next:active'

    card_owner = CharField(
        label="Card Owner",
        help_text="Please enter your name as noted on your credit card.",
    )
    card_number = RegexField(
        r'^(\d{16}|\d{4}\s\d{4}\s\d{4}\s\d{4})$',
        label="Card Number",
        widget=TextInput(attrs={'placeholder': 'xxxx xxxx xxxx xxxx'}),
        help_text="Please enter your 16 digit credit card number.",
    )
    previous = Activator(
        label="Previous",
        widget=Button(
            action='activate("apply")',
            button_variant=ButtonVariant.SECONDARY,
            icon_path='formset/icons/chevron-left.svg',
            icon_left=True,
        )
    )
    submit = Activator(
        label="Submit",
        widget=Button(
            action='submit -> reload !~ scrollToError',
            button_variant=ButtonVariant.PRIMARY,
            attrs={'class': 'float-end'},
        )
    )


class CheckoutCollection(StepperCollection):
    legend = "Checkout your Order"
    contact = ContactForm()
    shipping = ShippingForm()
    payment = PaymentForm()
