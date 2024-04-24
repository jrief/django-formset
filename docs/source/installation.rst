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

.. note:: If you upgrade from version 0.13 or lower, please read the :ref:`changes` as in version 1
	there some breaking changes have been introduced.

.. rubric:: Include Stylesheets

If the CSS framework to be used is installed via ``npm``, it is strongly suggest to configure the
lookup path as

.. code-block:: python

	STATICFILES_DIRS = [
	    ...
	    ('node_modules', BASE_DIR / 'node_modules'),
	]

Assure that ``BASE_DIR`` points onto the root of your project. By doing so, the CSS file for
Bootstrap (and all other assets in ``node_modules``) can be included as

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

When loading CSS files from other domains such as a CDN or Google Fonts, then use
``<link href="https://cdn.somedomain.xyz" crossorigin="anonymous">``. This is because
**django-formset** parses some CSS rules, but Google Chrome refuses to do that for files from
foreign origins.

There are two optional CSS files, which might be imported depending on the application's setup:

.. code-block:: django

	<link href="{% static 'formset/css/bootstrap5-extra.css' %}" rel="stylesheet">

It adjusts the styling of some widget. Useful if used in a Bootstrap 5 context. 

.. code-block:: django

	<link href="{% static 'formset/css/collections.css' %}" rel="stylesheet">

This adds borders, backgrounds and some icons to form collections. Mandatory if used in combination
with :ref:`collections-with-siblings`, otherwise neither an "Add" nor a "Delete" button will be
rendered. This style definition style sheet can be applied to all CSS frameworks. 

.. rubric:: Include JavaScript

Only one JavaScript file must be included into the head or body of the main template. It is the file
providing the functionality of our web components:

.. code-block:: django

	{% load static %}
	...
	<head>
	  ...
	  <script type="module" src="{% static 'formset/js/django-formset.js' %}"></script>
	  ...
	</head>

This file is kept rather small as it only provides the core functionality. Additional dependencies
required for all the extra widgets are loaded on demand, if that specific component is used.

.. note:: The provided JavaScript file is optimized for modern browsers, which can handle
	EcmaScript-ES2020, or later. These browsers are Chrome 94+, Edge 94+, Firefox 93+, Safari 15+
	and Opera 81+. In the rare occasion that you have to support a legacy browser, choose an
	appropriate target from the TypeScript build options and recompile the sources.

If you're wondering where **django-formset** keeps the styles for all the widgets it provides, then
here is a short explanation: It doesn't need any framework specific style sheets, instead
**django-formset** relies on the styling definitions of the underlying CSS framework rather than
imposing their own styles on each component shipped with this library. These styles are extracted
from the existing HTML elements such as ``<input>``, ``<select>``, etc. They then are applied to the
custom elements of the web components. This is why this library adopts itself to the given CSS
framework without the need to provide a dedicated style sheet.
