.. _fieldsets:

=========
Fieldsets
=========

In HTML the ``<form>``-element is just a data-abstraction layer. It has no display properties and is
not intended to be styled or annotated. Its purpose is to group one or more input fields, in order
to submit their gathered input data to the server altogether.

On the other side, we might want to visually group those input fields and optionally add a legend
tag to create a caption for the form. We also might want to group related input fields visually by
surrounding them with a border. For this purpose the HTML standard defines the ``<fieldset>`` tag.
Django itself does not offer any abstraction for this HTML tag. If one wants to use it, this has to
be done on the template level when rendering the form.

To fill this gap, **django-formset** introduces a Python class to handle the ``<fieldset>``-element.
From a technical point of view, a fieldset behaves exactly like a single form and in HTML it always
must be wrapped inside a ``<form>``-element. If we want to use more than one fieldset, then we have
to group them using :ref:`collections`, just as we would do with normal forms.

Another purpose of using fieldsets, apart from adding a border and legend to a form, is to use
:ref:`conditionals`. This allows us to hide or disable the whole fieldset depending on the context
of other fields.


Example
=======

In this example we use two forms nested in a ``FormCollection``. Remember, a ``Fieldset`` behaves
exactly as a ``Form`` instance and can be used as a replacement, although with additional styling
possibilities.

.. django-view:: import
	:hide-code:
	:hide-view:

	from formset.renderers.bootstrap import FormRenderer

.. django-view:: fieldset
	:view-function: CustomerView.as_view(extra_context={'framework': 'bootstrap'})

	from django.forms import fields, forms
	from formset.fieldset import Fieldset
	from formset.collection import FormCollection
	from formset.views import FormCollectionView

	class CustomerForm(Fieldset):
	    legend = "Customer"
	    hide_condition = 'register.no_customer'
	    recipient = fields.CharField(label="Recipient", required=False)
	    address = fields.CharField(label="Address", required=False)
	
	class RegisterForm(forms.Form):
	    no_customer = fields.BooleanField(
	        label="I'm not a customer",
	        required=False,
	    )
	
	class CustomerCollection(FormCollection):
	    customer = CustomerForm()
	    register = RegisterForm()
	    default_renderer = FormRenderer(
	        field_css_classes='mb-3',
	        fieldset_css_classes='border rounded p-3 mb-3',
	    )

	class CustomerView(FormCollectionView):
	    collection_class = CustomerCollection
	    template_name = "form-collection.html"
	    success_url = "/success"

.. note:: Bootstrap hides the border of fieldsets. Therefore in this example, we added a default
	renderer, to set the proper CSS classes for the given fieldset.

The interesting part of this collection is that we can hide the fieldset by clicking on the
checkbox named "I'm not a customer". This means that by using conditionals, we can dynamically
adjust the visibility of a complete form.

Remember to make the fields in the fieldset optional. Otherwise if the fieldset is hidden, the form
submission will fail without being able to give feedback which fields are missing. If you need a
specific validation logic, add it to the form's ``clean()``-method.
