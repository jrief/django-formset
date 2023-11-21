.. _phone-number-field:

==================
Phone Number Field
==================

In many applications we need an input field to enter a phone number. Unfortunately phone numbers
can be written in so many different formats that it is difficult to validate them using just
regular expressions. The best way to validate a phone number is to use a special library that can
parse and format the phone numbers according to the country's conventions.

Since users often enter a phone number in their local rather than international notation, the
component handling the input field should enforce entering the international prefix for the desired
country. This avoids ambiguities and is done by providing a dropdown list with all countries and
their international prefix.

On submission, phone numbers are saved in the E.164_ format. This is the international notation
starting with a ``+`` followed by the country code and the local number. For example, the German
number ``+49 30 1234567`` is saved as ``+49301234567``.

.. _E.164: https://en.wikipedia.org/wiki/E.164

Installation
============

We need to install a package providing the flag icons. This can be found in NodeJS:

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

Since we want to render the country names in the user's language, we need to set up
`the JavaScriptCatalog view`_ by configuring ``USE_I18N = True`` in the project's ``settings.py``.

.. _the JavaScriptCatalog view: https://docs.djangoproject.com/en/stable/topics/i18n/translation/#module-django.views.i18n

We also must provide a route to that view in the project's ``urls.py``:

.. code-block:: python

	from django.urls import path
	from django.views.i18n import JavaScriptCatalog

	urlpatterns = [
	    ...
	    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
	    ...
	]

Finally we must load the JavaScript file containing the translations for the given country names
when rendering our forms. Here we load this generated file to the ``<head>`` section of our
template:

.. code-block:: django

	<head>
	    ...
	    <script type="text/javascript" src="{% url 'javascript-catalog' %}"></script>
	    ...
	</head>

If we omit the latter, all country names will be rendered in English.


Usage
=====

In a Django form, a phone number field must be declared by using either a ``CharField`` or a
``RegexField``. If the latter is used, the regular expression must match the E.164 format, which is
``^\+\d{3,15}$``. An alternative is to use the ``PhoneNumberField`` provided by the
django-phonenumber-field_ package.

.. _django-phonenumber-field: https://github.com/stefanfoulis/django-phonenumber-field/

**django-formset** provides a widget that can be used to facilitate entering a phone number into a
field. This widget only performs client side validation, so unless you don't care about tampered
user input, it is a good idea to also validate the phone number on the server side using either the
already mentioned ``RegexField`` or a special validator.

.. django-view:: contact_form
	:caption: form.py

	from django.forms import fields, forms
	from django_countries import countries
	from formset.validators import phone_number_validator
	from formset.widgets import PhoneNumberInput

	class ContactForm(forms.Form):
	    phone_number = fields.CharField(
	        widget=PhoneNumberInput,
	        validators=[phone_number_validator],
	    )

As the controlling Django view, we can use a class inheriting from :class:`formset.views.FormView`,
as we did in all the other examples.

.. django-view:: phone_view
	:view-function: PhoneNumberView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'contact-result'}, form_kwargs={'auto_id': 'cf_id_%s'})
	:hide-code:

	from formset.views import FormView

	class PhoneNumberView(FormView):
	    form_class = ContactForm
	    template_name = "form.html"
	    success_url = "/success"


Extra Settings
==============

The following settings can be used to customize the behavior of the phone number widget:

* Adding ``"default-country-code": "XX"`` to the widget's ``attrs`` dictionary, preselects the
  named country, so that users must not enter their international prefix. Entering a foreign phone
  number is still possible. Remember to replace ``XX`` by the desired two-letter country code.
* Adding ``mobile-only: True`` to the widget's ``attrs`` dictionary, restricts the phone number to
  mobile phones only. This is useful if the number is required for sending SMS messages.

In this example we preselect the country code for Austria and restrict the phone number to mobile
phones only.

.. django-view:: sms_form
	:caption: form.py

	from django.forms import fields, forms
	from django_countries import countries
	from formset.validators import phone_number_validator
	from formset.widgets import PhoneNumberInput

	class SMSForm(forms.Form):
	    phone_number = fields.CharField(
	        widget=PhoneNumberInput(attrs={
	            "default-country-code": "AT",
	            "mobile-only": True,
	        }),
	        validators=[phone_number_validator],
	    )

.. django-view:: sms_view
	:view-function: SMSView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'sms-result'}, form_kwargs={'auto_id': 'sm_id_%s'})
	:hide-code:

	from formset.views import FormView

	class SMSView(FormView):
	    form_class = SMSForm
	    template_name = "form.html"
	    success_url = "/success"

In this form a user may for instance enter ``0664 1234567``, which immediately is converted to
``+43 664 1234567``. If however for example, he starts typing ``+49``, then the country code is
changed to Germany. The number is still validated against mobile phones though.


Rendering Phone Numbers
=======================

Phone numbers are saved in the E.164_ format, e.g. ``+49301234567``, which is not well readable for
humans. We usually want to display such a number in its local format, namely ``+49 30 1234567``.
This can be done by using the ``format_phonenumber`` template filter provided by the ``formset``
package. This filter takes a phone number in the E.164 format and converts it to the local format
according to the country's conventions.

This filter requires a special third party library not installed by default. To install it, run:

.. code-block:: bash

	pip install phonenumbers

.. note:: When using the django-phonenumber-field_ package, this library is already installed. The
	latter also provides similar formatting functionality. Please refer to their documentation for
	more information.

In our Django templates we then can use:

.. code-block:: django

	{% load phonenumbers %}
	...
	{{ phone_number|format_phonenumber }}

This renders a phone number in the local format, e.g.:

* in London, for instance as ``+44 20 1234 5678``
* in Berlin, for instance as ``+49 30 1234567``
* in New York, for instance as ``+1 212-123-4567``

In the rare case that all phone numbers belong to the same country, we can also render the phone
number without the international prefix using the template filter:

.. code-block:: django

	{{ phone_number|format_phonenumber:"national" }}

This for instance then renders the above phone number for New York as ``(212) 123-4567``.

However, I strongly advise against using this filter since it makes it hard to distinguish
phone numbers from different countries.


Implementation Details
======================

This ``django-phone-number`` widget is implemented using the npm package libphonenumber-js_. This
library implements a database with all countries, their landline- and mobile phone prefixes, and
their formatting conventions. It is a port of Google's libphonenumber library to JavaScript.

.. _libphonenumber-js: https://github.com/catamphetamine/libphonenumber-js
