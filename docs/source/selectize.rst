.. _selectize:

================
Selectize Widget
================

Rendering choice fields using a ``<select>``-element becomes quite impractical when there are too
many options to select from.

For this purpose, the Django admin backend offers so-called `auto complete fields`_, which loads a
filtered set of options from the server as soon as the user starts typing into the input field. This
widget is based on the Select2_ plugin, which itself depends upon jQuery, and hence it is not
suitable for us. Since **django-formset** aims to be JavaScript framework agnostic, it uses an
alternative widget written in pure JavaScript.

.. _auto complete fields: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#django.contrib.admin.ModelAdmin.autocomplete_fields
.. _Select2: https://select2.org/


Usage with fixed Number of Choices
==================================

Assume, we have an address form defining a ChoiceField_ to choose one of the past European Django
conferences. If this number exceeds say 25, then we should consider to render the select box using
the special widget :class:`formset.widgets.Selectize`:

.. _ChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.ChoiceField 

.. django-view:: conference_form

	from django.forms import fields, forms, widgets
	from formset.widgets import Selectize

	class ConferenceForm(forms.Form):
	    venue = fields.ChoiceField(
	        choices=[
	            (2009, "Praha"),
	            (2010, "Berlin"),
	            (2011, "Amsterdam"),
	            (2012, "Zürich"),
	            (2013, "Warszawa"),
	            (2014, "Île des Embiez"),
	            (2015, "Cardiff"),
	            (2016, "Budapest"),
	            (2017, "Firenze"),
	            (2018, "Heidelberg"),
	            (2019, "København"),
	            (2020, "Virtual"),
	            (2022, "Porto"),
	            (2023, "Edinburgh"),
	            (2024, "Vigo"),
	            (2025, "Dublin"),
	            (2026, "Αθήνα (Athens)"),
	            (2027, "Innsbruck"),
	        ],
	        widget=Selectize,
	    )

This widget waits for the user to type some characters into the input field for "``venue``". If the
entered string matches the name of one or more cities (even partially), then a list of options is
generated containing the matching cities. By adding more characters to the input field, that list
will shrink to only a few or eventually no entry. This makes the selection simple and comfortable.

.. django-view:: conference_view
	:view-function: SelectizeView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'conference-result'}, form_kwargs={'auto_id': 'cf_id_%s'})
	:hide-code:

	from formset.views import FormView 

	class SelectizeView(FormView):
	    form_class = ConferenceForm
	    template_name = "form.html"
	    success_url = "/success"


Usage with dynamic Number of Choices
====================================

Often we can't handle the choices using a static list. This happens for instance, when we store them
in a Django model. We then point a foreign key onto the chosen entry of that model. The above
example then can be rewritten by replacing the ChoiceField_ against a ModelChoiceField_. Instead of
``choices`` this field then requires an argument ``queryset``. For the form defined above, we use a
Django model named ``County`` with ``name`` as identifier. All counties we can select from, are now
stored in a database table.

.. _ModelChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.ModelChoiceField 

.. django-view:: county_form

	from django.forms import fields, forms, models, widgets
	from formset.widgets import Selectize
	from testapp.models import County

	class CountyForm(forms.Form):
	    county = models.ModelChoiceField(
	        queryset=County.objects.select_related('state'),
	        widget=Selectize(
	            search_lookup='name__icontains',
	            placeholder="Select a county",
	        ),
	    )

Here we instantiate the widget :class:`formset.widgets.Selectize` using the following arguments:

* ``search_lookup``: A Django `lookup expression`_. For choice fields with more than 50 options,
  this instructs the **django-formset**-library on how to look for other entries in the database. 
* ``group_field_name`` in combination with option groups. This field is used to determine the group
  name. See below.
* ``filter_by`` is a dictionary to filter options based on the value of other field(s). See below.
* ``placeholder``: The empty label shown in the select field, when no option is selected.
* ``attrs``: A Python dictionary of extra attributes to be added to the rendered ``<select>``
  element.

.. _lookup expression: https://docs.djangoproject.com/en/stable/ref/models/lookups/#lookup-reference

.. django-view:: county_view
	:view-function: CountyView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'county-result'}, form_kwargs={'auto_id': 'co_id_%s'})
	:hide-code:

	class CountyView(SelectizeView):
	    form_class = CountyForm


Grouping Select Options
-----------------------

Sometimes it may be desirable to group options the user may select from.

In the United States there are 3143 counties, many of them sharing the same name. When rendering
them inside a select box, it would be rather unclear which county belongs to which state. For this
purpose, HTML provides the element ``<optgroup>``. Other than visually grouping options to select
from, this element has no other effect. Fortunately our ``Selectize`` widget mimicks that feature
and so we can group all counties by state by rewriting our form as:

.. django-view:: grouped_county_form

	class GroupedCountyForm(forms.Form):
	    county = models.ModelChoiceField(
	        label="County",
	        queryset=County.objects.select_related('state'),
	        widget=Selectize(
	            search_lookup='name__icontains',
	            group_field_name='state',
	            placeholder="Select a county"
	        ),
	        required=True,
	    )

.. django-view:: grouped_county_view
	:view-function: GroupedCountyView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'grouped-county-result'}, form_kwargs={'auto_id': 'gc_id_%s'})
	:hide-code:

	class GroupedCountyView(SelectizeView):
	    form_class = GroupedCountyForm

Here we grouped the counties by state. To achieve this, we have to change the widget in the field
``county`` and configure how to group them. By using the attribute ``group_field_name``, the
``Selectize``-widget uses the named field from the model specified by the queryset for grouping.

When rendered, the ``<option>`` elements then are grouped inside ``<optgroup>``-s using the state's
name as their label:


Filtering Select Options
------------------------

As we have seen in the previous example, even grouping too many options might not be a user-friendly
solution. This is because the user has to type a string, at least partially. So the user already
must know what he’s looking for, but this approach is not always practical. Many of the counties
share the same name. For instance, there are 34 counties named “Washington”, 26 named “Franklin” and
24 named “Lincoln”. Using an auto-select field, would just show a long list of eponymous county
names.

In many use cases, the user usually knows in which state the desired county is located. So it would
be useful if the selection field offers a reduced set of options, namely the counties of just
that state. Therefore let's create a form with adjacent fields for preselecting options:

.. django-view:: filtered_county_form

	from testapp.models import State

	class FilteredCountyForm(forms.Form):
	    state = models.ModelChoiceField(
	        label="State",
	        queryset=State.objects.all(),
	        widget=Selectize(
	            search_lookup='name__icontains',
	            placeholder="First, select a state"
	        ),
	        required=False,
	    )
	    county = models.ModelChoiceField(
	        label="County",
	        queryset=County.objects.select_related('state'),
	        widget=Selectize(
	            search_lookup=['name__icontains'],
	            filter_by={'state': 'state_id'},
	            placeholder="Then, select a county"
	        ),
	        required=True,
	    )

This form shows the usage of two adjacent fields, where the first field's value is used to filter
the options for the next field. Here with the field **state**, the user can make a preselection of
the state. When the state is changed, the other field **county** gets filled with all counties
belonging to that selected state.

To enable this feature, the widget ``Selectize`` accepts the optional argument ``filter_by`` which
contains a dictionary such as ``{'state': 'state_id'}`` defining the lookup expression on the given
queryset. Here each key maps to an adjacent field and its value contains a lookup expression.

.. django-view:: filtered_county_view
	:view-function: FilteredCountyView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'filtered-county-result'}, form_kwargs={'auto_id': 'fc_id_%s'})
	:hide-code:

	class FilteredCountyView(SelectizeView):
	    form_class = FilteredCountyForm

Setting up forms using filters, can improve the user experience, because it reduces the available
options to choose from. This might be a more friendly alternative rather than using option groups.


Filtering using the ``django-filter`` library
---------------------------------------------

It sometimes might be more convenient to use the popular `django-filter`_ library to filter the
options for a select field. This library offers a more flexible way and allows the developer to
filter the options based on a combination of various fields. The following example shows how to
implement the above example inheriting from a ``DjangoFilterSet``:

.. _django-filter: https://django-filter.readthedocs.io/en/stable/

.. django-view:: use_filterset_county_form
	:caption: forms.py
	:emphasize-lines: 30

	from django_filters import FilterSet, ModelChoiceFilter

	class StateFilterSet(FilterSet):
	    state = ModelChoiceFilter(
	        queryset=State.objects.all(),
	    )
	
	    @property
	    def qs(self):
	        parent_qs = super().qs
	        if state := self.request.GET.get('filter-state'):
	            return parent_qs.filter(state=state)
	        return parent_qs

	class FilteredCountyFormUsingFilterSet(forms.Form):
	    state = models.ModelChoiceField(
	        label="State",
	        queryset=State.objects.all(),
	        widget=Selectize(
	            search_lookup='name__icontains',
	            placeholder="First, select a state"
	        ),
	        required=False,
	    )
	    county = models.ModelChoiceField(
	        label="County",
	        queryset=County.objects.select_related('state'),
	        widget=Selectize(
	            search_lookup=['name__icontains'],
	            use_filter_set=StateFilterSet,
	            placeholder="Then, select a county"
	        ),
	        required=True,
	    )

Here we use the argument ``use_filter_set`` instead of ``filter_by`` when declaring the widget used
by the field the select the county. This argument expects a class inheriting from ``FilterSet``,
here it's named ``StateFilterSet``. On this filterset we can declare one or more filter fields to
be applied to the queryset. Remember that all fields from this filterset are prefixed with
``filter-<fieldname>`` when being fetched by client side of the **django-formset** library. These
fields then must be extracted from the ``request.GET`` object. In this example this happens inside
the property ``qs``. The filter ``state`` is then used to filter the queryset of the counties.

.. django-view:: use_filterset_county_view
	:view-function: UseFilterSetCountyView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'use-filter-set-county-result'}, form_kwargs={'auto_id': 'ufs_id_%s'})
	:hide-code:

	class UseFilterSetCountyView(SelectizeView):
	    form_class = FilteredCountyFormUsingFilterSet

The ``django-filter`` library is an optional dependency. It only must be installed if you want to
use the ``use_filter_set`` feature. No part of the **django-formset** library imports any modules
from that library.


.. _selectize-multiple:

Selectize Multiple Widget
=========================

If the form field for "``county``" shall accept more than one selection, in Django we replace it by
a :class:`django.forms.fields.MultipleChoiceField`. The widget then used to handle such an input
field also must be replaced. For this purpose **django-formset** offers the special widget
:class:`formset.widgets.SelectizeMultiple` to handle more than one option to select from. From a
functional point of view, this behaves similar to the ``Selectize`` widget described before. But
instead of replacing a chosen option by another one, selected options are lined up to build a set of
options. Again, we can group and filter the given options, as shown in the two previous examples.
This example rewrites the grouped options with a ``SelectizeMultiple`` widget: 

.. django-view:: grouped_counties_form

	from formset.widgets import SelectizeMultiple

	class GroupedCountiesForm(forms.Form):
	    county = models.ModelMultipleChoiceField(
	        label="County",
	        queryset=County.objects.select_related('state'),
	        widget=SelectizeMultiple(
	            search_lookup='name__icontains',
	            group_field_name='state',
	            placeholder="Select up to 5 counties"
	        ),
	        required=True,
	    )

.. django-view:: grouped_counties_view
	:view-function: GroupedCountiesView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'grouped-counties-result'}, form_kwargs={'auto_id': 'gmc_id_%s'})
	:hide-code:

	class GroupedCountiesView(SelectizeView):
	    form_class = GroupedCountiesForm

By default a ``SelectizeMultiple`` widget can accept up to 5 different options. This limit can be
adjusted by increasing the argument of ``max_items``. This value however shall not exceed more than
say 15 items, otherwise the input field might become unmanageable. If you need a multiple select
field able to accept hundreds of items, consider using the :ref:`dual-selector` widget.


Options with Sublabels
======================

.. version-added:: 2.1

Sometimes one label is not enough to describe an option. For instance, when selecting a county, it
might be useful to show the state's name below the county name. The ``Selectize`` widget allows us
to render the options by specifying a sublabel. For this purpose, Django offers the method
label_from_instance_. By default, this method should return a string which is used as the label for
all its options. If we also want to render sublabels, we can return a dictionary. The value of
the ``label`` keys then is used as their main labels, whereas the value of the ``sublabel`` keys is
used for showing their sublabel.

.. _label_from_instance: https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.ModelChoiceField.iterator

In this example we create a special form field and override the method ``label_from_instance`` using
a special field class.

.. django-view:: county_sublabeled_form

	from django.forms import fields, forms, models, widgets
	from formset.widgets import Selectize
	from testapp.models import County

	class CountyChoiceField(models.ModelChoiceField):
	    def label_from_instance(self, obj):
	        return {'label': obj.name, 'sublabel': obj.state.name}

	class CountySublabeledForm(forms.Form):
	    county = CountyChoiceField(
	        queryset=County.objects.select_related('state'),
	        widget=Selectize(
	            search_lookup='name__icontains',
	            placeholder="Select a county",
	        ),
	    )

.. django-view:: county_sublabeled_view
	:view-function: CountySublabeledView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'county-sublabeled-result'}, form_kwargs={'auto_id': 'csl_id_%s'})
	:hide-code:

	class CountySublabeledView(SelectizeView):
	    form_class = CountySublabeledForm


Alternative labels for chosen items
-----------------------------------

When opening the dropdown, the county names are used as the default label, whereas their state names
are used as sublabels.

In the previous examples, the chosen county showed the state name in brackets. If we want to render
the label of the selected options differently, we can return a key ``itemlabel`` in the dictionary
returned by the method ``label_from_instance``. By rewriting the above field class to:

.. code-block:: python

	class CountyChoiceField(models.ModelChoiceField):
	    def label_from_instance(self, obj):
	        return {
	            'label': obj.name,
	            'sublabel': obj.state.name,
	            'itemlabel': f"{obj.name} ({obj.state.name})",
	        }

the chosen county will for example again be rendered as "Monterey (CA)" instead of just "Monterey".


Handling ``ForeignKey`` and ``ManyToManyField``
===============================================

If we create a form out of a Django model, we explicitly have to tell it to either use the
``Selectize`` or the ``SelectizeMultiple`` widget. Otherwise Django will use the default HTML
``<select>`` or ``<select multiple>`` fields, which are not user friendly for big datasets.

Say that we have an address model using  a foreign key to existing cities:

.. code-block:: python
	:caption: models.py

	from django.db import models

	class AddressModel(models.Model):
	    # other fields
	
	    city = models.ForeignKey(
	        CityModel,
	        verbose_name="City",
	        on_delete=models.CASCADE,
	    )

then when creating the corresponding Django form, we must replace the default widget ``Select``
against our special widget ``Selectize``:

.. code-block:: python
	:caption: forms.py

	from django.forms import models
	from formset.widgets import Selectize

	class AddressForm(models.ModelForm):
	    class Meta:
	        model = AddressModel
	        fields = '__all__'
	        widgets = {
	            # other fields
	            'city': Selectize(search_lookup='label__icontains'),
	        }

The argument ``search_lookup`` is used to build the search query.

If we want to allow the user to select more than one city, we have to replace the ``ForeignKey``
against a ``ManyToManyField`` – and conveniently rename "city" to "cities". Then in the above
example, we'd have to replace the ``Selectize`` widget against ``SelectizeMultiple``:

.. code-block:: python
	:caption: forms.py

	from django.forms import models
	from formset.widgets import SelectizeMultiple

	class AddressForm(models.ModelForm):
	    class Meta:
	        model = AddressModel
	        fields = '__all__'
	        widgets = {
	            # other fields
	            'cities': SelectizeMultiple(search_lookup='label__icontains'),
	        }

Endpoint for Dynamic Queries 
============================

Remember that all views connecting forms using the ``Selectize`` or ``SelectizeMultiple`` widget
must inherit from :class:`formset.views.IncompleteSelectResponseMixin`. This mixin handles the
endpoint for our lookups.

In comparison to other libraries offering autocomplete fields, such as `Django-Select2`_,
**django-formset** does not require developers to add an explicit endpoint to the URL routing.
Instead it shares the same endpoint for form submission as for querying for extra options out of the
database. This means that the form containing a field using the ``Selectize`` widget *must* be
controlled by a view inheriting from :class:`formset.views.IncompleteSelectResponseMixin`.

.. note:: The default view offered by **django-formset**, :class:`formset.views.FormView` already
	inherits from ``IncompleteSelectResponseMixin``.

.. _Django-Select2: https://django-select2.readthedocs.io/en/latest/


Adding extra Options on the Fly
===============================

In some cases, the user might not find the desired option in the list of choices. For this use-case
the Tom-Select library offers a feature to `add new options on the fly`_. In the context of Django
models such a feature could only be offered with limited functionality, because the user then could
only add a single string to the referenced model.

Instead, **django-formset** offers a more flexible solution. By adding a button to a collection,
which opens a form dialog, the user can create a new instance with all required model fields.
For details please refer to the page on :ref:`dialog-model-forms`.

.. _add new options on the fly: https://tom-select.js.org/examples/create-filter/


Implementation Details
======================

The client part of the ``Selectize`` widget relies on Tom-Select_ which itself is a fork of the
popular `Selectize.js`_-library, but rewritten in pure TypeScript and without any other external
dependencies. This made it suitable for the client part of **django-formset**, which itself is a
self-contained JavaScript library compiled out of TypeScript.

.. _Tom-Select: https://tom-select.js.org/
.. _Selectize.js: https://selectize.dev/
