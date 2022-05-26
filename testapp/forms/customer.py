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
    This Form Collection shows the usage of a ``Fieldset``. The ``Fieldset`` behaves excatly like a ``Form``
    but wraps the form fields inside a ``<fieldset>``-element and usually is surrounded by a border. In HTML,
    fieldsets are used to visually group fields.

    .. code-block:: python

        from formset.fieldset import Fieldset

        class CustomerForm(Fieldset):
            legend = "Customer"
            hide_if = 'register.no_customer'

            name = fields.CharField(label="Recipient")
            # … more fields

    A fieldset typically has a ``<legend>``- element. We use the attribute ``legend``  to name this
    fieldset.

    By adding the property ``show_if``, ``hide_if`` or ``disable_if`` we can hide the complete
    fieldset or disable all of its fields, depending on any value available in our Formset.

    Here we have a collection of two forms, where the first one inherits from ``Fieldset`` instead
    of ``Form``. The other form just contains a checkbox labled *"I'm not a customer"*.

    .. code-block:: python

        class RegisterForm(forms.Form):
            no_customer = fields.BooleanField(
                label="I'm not a customer",
                required=False,
            )

    In this example we add ``hide_if = 'register.no_customer'`` to the class ``CustomerForm``. Whenever someone
    clicks onto that checkbox, the whole upper fieldset is hidden.

    Finally we group those two forms into one collection namend ``CustomerCollection`` to build one submittable
    entity.

    .. code-block:: python

        class CustomerCollection(FormCollection):
            customer = CustomerForm()
            register = RegisterForm()
    """

    customer = CustomerForm()

    register = RegisterForm()
