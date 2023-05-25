.. _renderers:

==============
Form Renderers
==============

Since Django-4.0 each form can specify its own renderer_. This is important, because it separates
the representation layer from the logical layer of forms. And it allows us to render the same form
for different CSS frameworks without modifying a single field. The only thing we have to do, is to
replace the default form renderer with an alternative one.

.. _renderer: https://docs.djangoproject.com/en/4.0/ref/forms/renderers/#the-low-level-render-api

Form Grid Example
=================

Say, we have a Django form to ask for the recipient's address, consisting of three fields:
``recipient``, ``postal_code`` and ``city``. Usually we prefer to keep the postal code and the
destination city on the same row. When working with the Bootstrap framework, we therefore want to
use the `form grid`_ for form layouts that require multiple columns, varied widths, and additional
alignment options.

To properly render this form, we therefore have to add the CSS classes ``row`` and ``col-XX`` to the
wrapping elements. One possibility is to create a template and style each field individually; this
is the procedure described in :ref:`field_by_field`. This however requires creating a template for
each form, which contradicts the DRY-principle.

.. _form grid: https://getbootstrap.com/docs/5.2/forms/layout/#form-grid

Rendering the form using our well known templatetag ``{% render_form form … %}`` unfortunately does
not work here, because we can not add different CSS classes to the three given fields. Using that
templatetag only allows us to generically specify CSS classes for labels, field groups and input
fields, but not on an individual level.

We therefore parametrize the provided renderer class. For each supported CSS framework, there is a
specialized ``FormRenderer`` class. For Bootstrap, that class can be found at
:class:`formset.renderers.bootstrap.FormRenderer`. The form to be rendered, hence requires a
parametrized renderer. Since **django-formset** renders forms using a different notation for field
names, that form must additionally inherit from the special mixin :class:`formset.utils.FormMix`. It
would thus be written as:

.. django-view:: address_form
	:caption: forms.py

	from django.forms import forms, fields
	from formset.renderers.bootstrap import FormRenderer
	from formset.utils import FormMixin
	
	class AddressForm(FormMixin, forms.Form):
	    default_renderer = FormRenderer(
	        form_css_classes='row',
	        field_css_classes={
	            '*': 'mb-2 col-12',
	            'postal_code': 'mb-2 col-4',
	            'city': 'mb-2 col-8'
	        },
	    )

	    recipient = fields.CharField(label="Recipient", max_length=100)
	    postal_code = fields.CharField(label="Postal Code", max_length=8)
	    city = fields.CharField(label="City", max_length=50)

Since that form now knows how to render itself, it does not require the templatetag ``render_form``
anymore. It instead can be rendered just by string expansion. The template to render that form hence
simplifies down to:

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {{ form }}
	  <p class="mt-3">
	    <button type="button" click="submit -> proceed" class="btn btn-primary">Submit</button>
	    <button type="button" click="reset" class="ms-2 btn btn-warning">Reset to initial</button>
	  </p>
	</django-formset>

When rendered in a Bootstrap-5 environment, that form will look like

.. django-view:: address_view
	:view-function: AddressView.as_view(extra_context={'framework': 'bootstrap'})
	:hide-code:

	from formset.views import FormView 

	class AddressView(FormView):
	    form_class = AddressForm
	    template_name = "form-extended.html"
	    success_url = "/success"

Here we pass a few CSS classes into the renderer. In ``form_css_classes`` we set the CSS class added
to the ``<form>`` element itself. In ``field_css_classes`` we set the CSS classes for the field
groups. If this is a string, the given CSS classes are applied to each field. If it is a dictionary,
then we can apply those CSS classes to each field individually, by using the field's name as a
dictionary key. The key ``*`` stands for the fallback and its value is applied to all fields which
are not explicitly listed in that dictionary.


Inline Form Example
===================

By using slightly different parameters, a form can be rendered with labels and input fields side
by side, rather than beneath each other. This can simply be achieved by replacing the form renderer
using these parameters.

.. code-block:: python

	from formset.renderers.bootstrap import FormRenderer

	class AddressForm(forms.Form):
	    default_renderer = FormRenderer(
	        field_css_classes='row mb-3',
	        label_css_classes='col-sm-3',
	        control_css_classes='col-sm-9',
	    )

	    # form fields as above

When rendered in a Bootstrap-5 environment, that form will look like:

.. django-view:: address_inline
	:view-function: AddressView.as_view(extra_context={'framework': 'bootstrap'}, form_kwargs={'renderer': FormRenderer(field_css_classes='row mb-3', label_css_classes='col-sm-3', control_css_classes='col-sm-9')})
	:hide-code:

In this example we don't use any field specific CSS classes, therefor we can achieve the same effect
by rendering this form using our well known templatetag ``render_form`` with these parameters:

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {% render_form form "bootstrap" field_classes="row mb-3" label_classes="col-sm-3" control_classes="col-sm-9" %}
	  <div class="offset-sm-3">
	    <button type="button" click="submit -> proceed" class="btn btn-primary">Submit</button>
	    <button type="button" click="reset" class="ms-2 btn btn-warning">Reset to initial</button>
	  </div>
	</django-formset>


Rendering Collections
=====================

When rendering form collections we have to specify at least one default renderer, otherwise all
member forms will be rendered unstyled.


API
===

**django-formset** provides a form renderer for each supported framework.

.. autoclass:: formset.renderers.default.FormRenderer
