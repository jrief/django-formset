.. _installation:

============
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


.. rubric:: Include Stylesheets

If the CSS framework to be used is installed via ``npm``, I strongly suggest to configure the lookup
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

Other CSS frameworks behave similarly. Except for Tailwind CSS, **django-formset** provides only
two very short CSS files. This is because it relies on the styling definitions of the underlying CSS
framework rather than imposing their own styles on the components shipped with this library.

.. note:: When loading CSS files from other domains such as a CDN or Google Fonts, then use
	`<link href="…" crossorigin="anonymous">`. This is because **django-formset** parses some CSS
	rules, but Google Chrome refuses to do that for files from foreign origins.

There are two optional CSS files, which might be imported depending on the application's setup:

.. code-block:: django

	<link href="{% static 'formset/css/bootstrap5-extra.css' %}" rel="stylesheet">

It adjusts the styling of the Dual Selector widget. Useful if used in a Bootstrap 5 context. 

.. code-block:: django

	<link href="{% static 'formset/css/collections.css' %}" rel="stylesheet">

This adds borders, backgrounds and some icons to form collections. Mandatory if used in combination
with :ref:`collections-with-siblings`, otherwise neither an "Add" nor a "Delete" button will be
rendered. This style definition style sheet can be applied to all CSS frameworks. 

Only one JavaScript file has to be included into the head or body of the main template:

.. rubric:: Include JavaScript

Many components from Bootstrap require their own JavaScript. This can optionally be included in a
very similar way as shown for the CSS above. One JavaScript file which always must be included is
that one, providing the functionality of our web component:

.. code-block:: django

	{% load static %}
	...
	<head>
	  ...
	  <script type="module" src="{% static 'formset/js/django-formset.js' %}"></script>
	  ...
	</head>

.. note:: The provided JavaScript file is optimized for modern browsers, which can handle
	EcmaScript-ES2020, or later. These browsers are Chrome 94+, Edge 94+, Firefox 93+, Safari 15+
	and Opera 81+. In the rare occasion that you have to support a legacy browser, choose an
	appropriate target from the TypeScript build options and recompile the sources.
