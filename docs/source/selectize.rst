.. _selectize:

The Selectize Widget
====================

Rendering choice fields using a ``<select>``-element becomes quite impractical when there are too
many options to select from. For this purpose, the Django admin backend offers so called
`auto complete fields`_, which loads a filtered set options from the server as soon as the user
starts typing into the input field. This widget is based on the Select2_ plugin, which itself
depends upon jQuery, and hence it is not suitable for **django-formset**, which aims to be Framework
independent.

.. _auto complete fields: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#django.contrib.admin.ModelAdmin.autocomplete_fields
.. _Select2: https://select2.org/


Usage with fix Number of Choices
--------------------------------

Assume, we have an address form defining a ChoiceField_ to choose from a city. If this number of
cities exceeds say 25, we should consider to render the select box using the special widget
:class:`formset.widgets.Selectize`:

.. _ChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.ChoiceField 

.. code-block:: python

	from django.forms import fields, forms, widgets
	from formset.widgets import Selectize

	class AddressForm(forms.Form):
	    # other fields

	    city = fields.ChoiceField(
	        choice=[(1, "London"), (2, "New York"), (3, "Tokyo"), (4, "Sidney"), (5, "Vienna")]
	        widget=Selectize,
	    )

This widget waits for the user to type some characters into the input field for city. If the entered
string matches the name of one or more cities (event partially), then a list of options is generated
containing the matching cities. By adding more characters to the input field, that list will shrink
to only a few or event no entry. This makes the selection simple and comfortable.


Usage with dynamic Number of Choices
------------------------------------

Sometimes we don't want to handle the choices using a static list. For instance, when we store them
in a Django model, we point a foreign key onto the choosen entry of that model. The above example
then can be rewritten by replacing the ChoiceField_ against a ModelChoiceField_. Instead of
``choices`` this field requires a ``queryset`` as parameter. For the form we defined above, we
use a Django model named ``Cities`` with ``name`` as identifier. All cities we can select from,
are now stored in a database table.

.. _ModelChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.ModelChoiceField 

.. code-block:: python

	from django.forms import fields, forms, models, widgets
	from formset.widgets import Selectize

	class AddressForm(forms.Form):
	    # other fields

	    city = models.ModelChoiceField(
	        queryset=Cities.objects.all(),
	        widget=Selectize(
	            search_lookup='name__icontains',
	            placeholder="Choose a city",
	        ),
	    )

Here we instantiate the widget :class:`formset.widgets.Selectize` using the following parameters:

* ``search_lookup``: A Django `lookup expression`_. For choice fields with more than 50 options,
  this instructs the **django-formset**-library on how to look for other entries in the database. 
* ``placeholder``: The empty label shown in the select field, when no option is selected.
* ``attrs``: A Python dictionary of extra attributes to be added to the rendered ``<select>``
  element.

.. _lookup expression: https://docs.djangoproject.com/en/stable/ref/models/lookups/#lookup-reference


Endpoint for Dynamic Queries 
----------------------------

In contrast to other libraries offering autocomplete fields, such as `Django-Select2`_,
**django-formset** does not require to add an explicit endpoint to the URL routing. Instead it
shares the same endpoint for form submission as for querying for extra options out of the database.
This means that the form containing a field using the ``Selectize`` widget *must* be controlled by
a view inheriting from :class:`formset.views.SelectizeResponseMixin`.

.. note:: The default view offered by **django-formset**, :class:`formset.views.FormView` already
	inherits from ``SelectizeResponseMixin``.

.. _Django-Select2: https://django-select2.readthedocs.io/en/latest/


Implementation Details
----------------------

The client part of the ``Selectize`` widget relies on Tom-Select_ which itself is a fork of the
popular `Selectize.js`_-library, rewritten in pure TypeScript and without any external dependencies.
This made it suitable for the client part of **django-formset**, which itself is a self-contained
JavaScript library compiled out of TypeScript.

.. _Tom-Select: https://tom-select.js.org/
.. _Selectize.js: https://selectize.dev/
