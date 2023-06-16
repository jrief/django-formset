.. _form-renderer:

=============
Form Renderer
=============

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
	    <button type="button" df-click="submit -> proceed" class="btn btn-primary">Submit</button>
	    <button type="button" df-click="reset" class="ms-2 btn btn-warning">Reset to initial</button>
	  </p>
	</django-formset>

When rendered in a Bootstrap-5 environment, that form will look like

.. django-view:: address_view
	:view-function: AddressView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'address-result'}, form_kwargs={'auto_id': 'af_id_%s'})
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
	:view-function: AddressView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'address-inline-result'}, form_kwargs={'renderer': FormRenderer(field_css_classes='row mb-3', label_css_classes='col-sm-3', control_css_classes='col-sm-9'), 'auto_id': 'ai_id_%s'})
	:hide-code:

In this example we don't use any field specific CSS classes, therefor we can achieve the same effect
by rendering this form using our well known templatetag ``render_form`` with these parameters:

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {% render_form form "bootstrap" field_classes="row mb-3" label_classes="col-sm-3" control_classes="col-sm-9" %}
	  <div class="offset-sm-3">
	    <button type="button" df-click="submit -> proceed" class="btn btn-primary">Submit</button>
	    <button type="button" df-click="reset" class="ms-2 btn btn-warning">Reset to initial</button>
	  </div>
	</django-formset>


Rendering Collections
=====================

When rendering form collections we have to specify at least one default renderer, otherwise all
member forms will be rendered unstyled.

Say that we have a collection with two forms, one to ask for the users names, the other for its
preferences.

.. django-view:: double_renderer
	:view-function: DoubleCollectionView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'collection-result'})
	:emphasize-lines: 34

	from django.forms import fields, forms, widgets
	from formset.collection import FormCollection
	from formset.renderers.bootstrap import FormRenderer
	from formset.views import FormCollectionView

	class UserForm(forms.Form):
	    legend = "Assigned License"
	    first_name = fields.RegexField(
	        r"^[A-Z][a-z -]+$",
	        label="First name"
	    )
	    last_name = fields.CharField(
	        label="Last name",
	        min_length=2,
	        max_length=50
	    )

	class PreferencesForm(forms.Form):
	    eating = fields.ChoiceField(
	        choices=[("🥗", "Vegan"), ("🧀", "Vegetarian"), ("🍗", "Carnivore")],
	        widget=widgets.RadioSelect,
	    )
	    drinking = fields.MultipleChoiceField(
	        choices=[
	            ("🚰", "Water"), ("🥛", "Milk"),
	            ("☕️", "Coffee"), ("🍵", "Tee"),
	            ("🍺", "Beer"), ("🥃", "Whisky"),
	            ("🥂", "White wine"), ("🍷", "Red wine"),
	        ],
	        widget=widgets.CheckboxSelectMultiple,
	    )

	class DoubleCollection(FormCollection):
	    default_renderer = FormRenderer(field_css_classes='mb-3')
	    user = UserForm()
	    preferences = PreferencesForm()

	class DoubleCollectionView(FormCollectionView):
	    collection_class = DoubleCollection
	    template_name = "form-collection.html"
	    success_url = "/success"

These two forms are rendered using the Bootstrap ``FormRenderer`` class as defined through the
argument ``default_renderer``.


Using multiple Renderers
========================

Sometimes using the same renderer for all form members does not produce the wanted results. We then
can overwrite the default renderer on a per member class as shown in this example:

.. django-view:: double_renderer_collection2

	class AlternativeCollection(FormCollection):
	    user = UserForm(renderer=FormRenderer(field_css_classes='mb-3'))
	    preferences = PreferencesForm(
	        renderer=FormRenderer(form_css_classes='row', field_css_classes='col'),
	    )

.. django-view:: double_renderer_view2
	:view-function: AlternativeCollectionView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'collection2-result'}, collection_kwargs={'auto_id': 'c2_id_%s'})
	:hide-code:

	class AlternativeCollectionView(FormCollectionView):
	    collection_class = AlternativeCollection
	    template_name = "form-collection.html"
	    success_url = "/success"

Here instead of using a default form renderer for the collection ``AlternativeCollection``, we pass
individually configured renderers to each form member of that collection. This also works for
collection members and can be applied to nested collections as well.
