.. _country-selectize:

====================================
Prepend the flag symbol to Countries
====================================

In many applications we need an input field to select one or more countries. To give a visually
better feedback, adding the flag symbol nearby the country's name is often a good idea.

Since **django-formset** does not know anything about the countries of this world, we first shall
install the package django-countries_. This package provides the Django model field
:class:`django_countries.fields.CountryField` and is rendered as a select field with all countries.
The field is based on the Django field :class:`django.db.models.CharField` and stores the country
code in the database. The country code is a two letter code, e.g. ``DE`` for Germany or ``US`` for
the United States, etc.

.. _django-countries: https://pypi.python.org/pypi/django-countries

.. code-block:: bash

	pip install django-countries

Strictly speaking, we do not need the package **django-countries** if we know the country codes and
names, and if we can provide them as a list of tuples. But the package **django-countries** is
useful, since it provides this list with all existing country names translated into more than 36
languages.

We also need to install a package providing the flag icons. This can be found in NodeJS:

.. code-block:: bash

	npm install flag-icons

Since we want to serve the flag icons directly from the ``node_modules`` directory, we need to
configure our Django ``setting.py`` as follows:

.. code-block:: python

	STATICFILES_DIRS = [
	    ...
	    ('node_modules', BASE_DIR / 'node_modules'),
	    ...
	]


Select a single Country
=======================

Whenever we need an input field to select a single country, **django-formset** offers the special
widget :class:`formset.widgets.CountrySelectize`. This can be used as a direct replacement for the
built-in widget :class:`django.forms.widgets.Select` and shall be used with the Django form field
:class:`django.forms.fields.ChoiceField`.

Here as an example, we create a simple address form with just a single field named ``country``.
This field is rendered as a select field showing all countries prefixed by their flags.

.. django-view:: country_form
	:caption: form.py

	from django.forms import fields, forms
	from django_countries import countries
	from formset.widgets import CountrySelectize

	class AddressForm(forms.Form):
	    country = fields.ChoiceField(
	        widget=CountrySelectize,
	        choices=countries,
	    )

Here for instance, we only use the list of countries provided by the package **django-countries**.

As the controlling Django view, we can use a class inheriting from :class:`formset.views.FormView`,
as we did in all the other examples.

.. django-view:: country_view
	:view-function: AddressView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'address-result'}, form_kwargs={'auto_id': 'ad_id_%s'})
	:hide-code:

	from formset.views import FormView

	class AddressView(FormView):
	    form_class = AddressForm
	    template_name = "form.html"
	    success_url = "/success"


Select multiple Countries
=========================

Whenever we need an input field to select multiple countries, **django-formset** offers the special
widget :class:`formset.widgets.CountrySelectizeMultiple`. This can be used as a direct replacement
built-in widget :class:`django.forms.widgets.SelectMultiple` and shall be used with the Django form
field :class:`django.forms.fields.MultipleChoiceField`.

Here as an example, we create a simple visitor form with just a single field named
``from_countries``. This field is rendered as a multiple select field showing all countries
prefixed by their flags.

.. django-view:: visitors_form
	:caption: form.py

	from django.forms import fields, forms
	from django_countries import countries
	from formset.widgets import CountrySelectizeMultiple

	class VisitorsForm(forms.Form):
	    countries = fields.MultipleChoiceField(
	        label="From Countries",
	        widget=CountrySelectizeMultiple(max_items=15),
	        choices=countries,
	        help_text="Select up to 15 countries",
	    )

Here for instance, we only use the list of countries provided by the package **django-countries**.

As the controlling Django view, we can use a class inheriting from :class:`formset.views.FormView`,
as we did in all the other examples.

.. django-view:: visitors_view
	:view-function: VisitorsView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'visitors-result'}, form_kwargs={'auto_id': 'vi_id_%s'})
	:hide-code:

	from formset.views import FormView

	class VisitorsView(FormView):
	    form_class = VisitorsForm
	    template_name = "form.html"
	    success_url = "/success"


Implementation Details
======================

Both widgets :class:`formset.widgets.CountrySelectize` and
:class:`formset.widgets.CountrySelectizeMultiple` are based on the widgets
:class:`formset.widgets.Selectize` and :class:`formset.widgets.SelectizeMultiple` respectively. The
only difference is that the selectable options prepend the flag symbol to their country name. This
is possible because the underlying JavaScript library TomSelect.js_ allows to customize nearly
every aspect of HTML.

.. _TomSelect.js: https://tom-select.js.org/
