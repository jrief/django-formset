.. _fieldsets:

=========
Fieldsets
=========

.. versionchanged:: 1.8

	Until version 1.7, the ``Fieldset`` class was a form wrapped into a ``<fieldset>``-element.
	This only made sense in combination with a ``FormCollection``. Since version 1.8, the
	``Fieldset`` class is a standalone entity to group multiple input fields into a ``<fieldset>``,
	just as the HTML standard defines it. Please adopt your code accordingly, if you used the
	``Fieldset`` class in version 1.7 or below.

In HTML the ``<form>``-element is just a data-abstraction layer. It has no display properties and is
not intended to be styled or annotated. Its purpose is to group one or more input fields, in order
to submit their gathered input data to the server altogether. This is especially true in
**django-formset**, where fields are only assigned to a form, but not their descendants in the DOM.

On the other side, we might want to visually group related input fields surrounding them with a
border and optionally add a legend tag to create a caption for them. For this purpose the HTML
standard defines the ``<fieldset>`` tag.

Django itself does not offer any abstraction for this HTML tag. If one wants to use it, this has to
be done on the template level when rendering the form. To fill this gap, **django-formset**
introduces the Python class :class:`formset.fieldset.Fieldset` to group multiple input elements into
a ``<fieldset>``-element. Such a ``Fieldset`` class can be used multiple times in a form. To
distinguish those fields, each field is prefixed with the fieldset's name, separated by a dot.

A fieldset accepts the optional string attribute ``legend``. This then is rendered as a
``<legend>``-element inside the ``<fieldset>``. A fieldset also accepts the optional string
attribute ``help_text``. This is rendered as a muted ``<p>``-element after the last field but inside
that fieldset.

Another purpose of using fieldsets, is to use :ref:`conditionals`. This allows us to hide or disable
the whole fieldset depending on the context of another field.


Example
=======

In this example form we use the same fieldset twice. The fieldset is used to group the input fields
for an address. Inside the form we then use that fieldset once for the billing- and once for the
shipping address. Since the billing address might be the same as the shipping address, we offer a
checkbox to hide the latter. Here we create this form to build one submittable entity:

.. django-view:: import
	:hide-code:
	:hide-view:

	from formset.renderers.bootstrap import FormRenderer

.. django-view:: fieldset
	:view-function: CustomerView.as_view(extra_context={'framework': 'bootstrap'}, form_kwargs={'renderer': FormRenderer(field_css_classes='mb-2', fieldset_css_classes='border rounded p-3 mb-3')}, template_name='form-extended.html')

	from django.forms import fields
	from formset.fieldset import Fieldset
	from formset.forms import Form
	from formset.views import FormView

	class AddressFieldset(Fieldset):
	    recipient = fields.CharField(
	        label="Recipient",
	        max_length=50,
	        required=False,
	    )
	    address = fields.CharField(
	        label="Address",
	        max_length=100,
	        required=False,
	    )

	class CustomerForm(Form):
	    billing_address = AddressFieldset(
	        legend="Billing Address",
	    )
	    shipping_address = AddressFieldset(
	        legend="Shipping Address",
	        hide_condition='use_billing_address',
	    )
	    use_billing_address = fields.BooleanField(
	        label="Use billing Address for shipping",
	        required=False,
	    )
	
	class CustomerView(FormView):
	    form_class = CustomerForm
	    success_url = "/success"

.. note:: Bootstrap hides the border of fieldsets. Therefore in this example, we added a special
	renderer, to set the CSS classes for the given fieldset to ``border rounded p-3 mb-3``.

The interesting part of this form is that we can hide the entire fieldset by clicking on the
checkbox labeled "Use billing Address for shipping". This means that by using conditionals, we can
dynamically adjust the visibility of a complete fieldset. In this example we add
``hide_condition = 'use_billing_address'`` when declaring the shipping address fieldset. Whenever
someone clicks onto that checkbox, that whole fieldset becomes hidden.

Remember to make the fields in the fieldset optional. Otherwise if the fieldset is hidden, the form
submission will fail without being able to give feedback which fields are missing. If you need a
specific validation logic, add it to the form's ``clean()``-method.


Initial Data
============

Since fieldsets are their own entity, they must be initialized using a special format for the keys
in the initial data dictionary. The key must be prefixed with the fieldset's name, followed by a dot
and then with the field's name. This is necessary to distinguish the data if multiple fieldsets are
used in the same form. For the above exaple the initial dictionary would look like this:

.. code-block:: python

	initial = {
		'billing_address.recipient': 'John Doe',
		'billing_address.address': 'Main Street 123',
		'shipping_address.recipient': 'Jane Doe',
		'shipping_address.address': 'Second Street 456',
	}


Nesting Fieldsets
=================

Fieldsets can be nested. This means that a fieldset can contain another fieldset. This is useful to
group fields even more. The field names then are prefixed with the parent fieldset's name, separated
by another dot.
