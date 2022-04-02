.. _installation:

Installation
============

Just as with any other third party Django app, install this package using

.. code-block:: shell

	pip install django-formset

and add this app to the project's ``settings.py``:

.. code-block:: python

	INSTALLED_APPS = [
	    ...
	    'formset',
	    ...
	]


Include Stylesheets
-------------------

If the CSS framework to be used is installed via ``npm``, I would suggest to configure the lookup
path as

.. code-block:: python

	STATICFILES_DIRS = [
	    ('node_modules', BASE_DIR / 'node_modules'),
	]

By doing so, the CSS file for Bootstrap can for instance be included as

.. code-block:: django

	{% load static %}
	...
	<head>
	  ...
	  <link href="{% static 'node_modules/bootstrap/dist/css/bootstrap.min.css' %}" rel="stylesheet">
	  ...
	</head>

other CSS frameworks behave similar. Except for Tailwind CSS, **django-formset** does not provide
any CSS files. This is because it relies on the styling definitions of the underlying CSS framework.
Only one JavaScript file has to be included into the head or body of the main template:


Include JavaScript
------------------

Many components from Bootstrap require their own JavaScript. This can optionally be included in a
very similar way as shown for the CSS above. One JavaScript file which always must be included is
that one, providing the functionality of our web component:

.. code-block:: django

	{% load static %}
	...
	<head>
	  ...
	  <script type="module" src="{% static 'formset/js/django-formset.min.js' %}"></script>
	  ...
	</head>

.. note:: The provided JavaScript file is optimized for modern browsers, which can handle
	EcmaScript-ES2020, or later. These browsers are Chrome 94, Edge 94, Firefox 93, Safari 15 and
	Opera 81. In the rare occasion, that you have to support a legacy browser, choose an appropriate
	target from the TypeScript build options and recompile the sources.
