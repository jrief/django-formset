from django.forms import fields, forms

from formset.fieldset import Fieldset
from formset.collection import FormCollection


class CustomerForm(Fieldset):
    legend = "Customer"
    hide_if = 'register.no_customer'

    name = fields.CharField(
        label="Recipient",
        max_length=100,
    )

    address = fields.CharField(
        label="Address",
        max_length=100,
    )

    phone_number = fields.RegexField(
        r'^\+?[0-9 .-]{4,25}$',
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
    """
    This form shows the usage of a ``Fieldset``. The ``Fieldset`` behaves excatly like a ``Form``
    but wraps the form fields inside a ``<fieldset>``-element. Such a fieldset has a ``<legend>``-
    element to name it and usually is surrounded by a border. In HTML, fieldsets are used to
    visually group fields.

    By adding the property ``show_if``, ``hide_if`` or ``disable_if`` we can hide the complete
    fieldset or disable all its fields.

    Here we have a collection of two forms, where the first one inherits from ``Fieldset`` instead
    of ``Form``. The other form just contains a checkbox labled *"I'm not a customer"*. In this
    example we add ``hide_if = 'register.no_customer'`` to that Fieldset class. Whenever someone
    clicks onto that checkbox, the whole upper fieldset is hidden.
    """

    customer = CustomerForm()

    register = RegisterForm()
