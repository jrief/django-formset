.. _fieldsets:

=========
Fieldsets
=========

.. versionchanged:: 2.0

	Until version 1.7, the ``Fieldset`` class was a form wrapped into a ``<fieldset>``-element.
	This only made sense in combination with a ``FormCollection``. Since version 2.0, the
	``Fieldset`` class is a standalone entity to group multiple input fields into a ``<fieldset>``,
	just as the HTML standard defines it. Please adopt your code accordingly, if you used the
	``Fieldset`` class from version 1.7 or below.

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

.. django-view:: fieldset_form

	from django.forms.fields import CharField, BooleanField
	from formset.fieldset import Fieldset
	from formset.forms import Form

	class AddressFieldset(Fieldset):
	    recipient = CharField(
	        label="Recipient",
	        max_length=50,
	        required=False,
	    )
	    address = CharField(
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
	    use_billing_address = BooleanField(
	        label="Use billing Address for shipping",
	        required=False,
	    )
	
.. django-view:: fieldset_view
	:view-function: CustomerView.as_view(extra_context={'framework': 'bootstrap'}, form_kwargs={'renderer': FormRenderer(field_css_classes='mb-2', fieldset_css_classes='border rounded p-3 mb-3')}, template_name='form-extended.html')
	:hide-code:

	from formset.renderers.bootstrap import FormRenderer
	from formset.views import FormView

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


Mapping Model Fields to Fieldset Fields
=======================================

The above example shows how to use fieldsets in a Django form. But what if we want to use a model
together with its form instead? Here we need a way to map the model fields to the fieldset fields.
This can be done using the same mechanism as shown in section :ref:`fields-mapping`.

Say, we have a Django model to describe a product. The title and the price are standard fields, but
in addition we also want to store the supplier's name.

.. code-block:: python
	:caption: models.py

	from django.db import models
	
	class ProductModel(models.Model):
	    title = models.CharField(max_length=50)
	    price = models.DecimalField(max_digits=5, decimal_places=2)
	    supplier_name = models.CharField(max_length=100)


In a typical form editing view, we would create a form inheriting from ``ModelForm`` and map all the
model fields to their corresponding form fields. Here however, we instead want the field named
``supplier_name`` to be part of the fieldset named ``Supplier`` and to be visually separated from
the remaining form.

.. django-view:: fieldset_mapping_form
	:caption: forms.py
	:emphasize-lines: 21

	from django.forms.fields import CharField
	from formset.fieldset import Fieldset
	from formset.forms import ModelForm
	from testapp.models.product import ProductModel

	class Supplier(Fieldset):
	    legend = "Supplier"

	    name = CharField(
	        label="Name",
	        max_length=100,
	    )

	class ProductForm(ModelForm):
	    supplier = Supplier()

	    class Meta:
	        model = ProductModel
	        fields = ['title', 'price', 'supplier_name']
	        fields_map = {
	            'supplier_name': 'supplier.name',
	        }
	
In order to achieve this, we use the ``fields_map`` attribute of the ``Meta``-class to map the model
field ``supplier_name`` to the field ``name`` from the given fieldset ``Supplier``. The key is the
name of the model field, and the value is the path to the field in the fieldset (ending with its
name and containing at least one dot). Remember to also add this model field to the ``Meta``'s
``fields`` attribute.

.. django-view:: fieldset_mapping_view
	:view-function: ProductView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'product-result'}, form_kwargs={'renderer': FormRenderer(field_css_classes='mb-2', fieldset_css_classes='border rounded p-3 mb-3')}, template_name='form-extended.html')
	:hide-code:

	from django.views.generic import UpdateView
	from formset.views import FormViewMixin
	from testapp.demo_helpers import SessionModelFormViewMixin

	class ProductView(SessionModelFormViewMixin, FormViewMixin, UpdateView):
	    model = ProductModel
	    form_class = ProductForm
	    template_name = 'form.html'

.. note:: After submission, the content of these form fields is stored in the database. Therefore
	after reloading this page, the same content will reappear in the form.
