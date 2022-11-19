.. _single-form:

==========================
Working with a single Form
==========================

In Django we typically assign a single form to a `FormView`_ class. Requests arriving with method
GET will create an empty or prefilled form instance and render it using the template specified in
the view class. This view class then is connected to our URL router:

.. _FormView: https://docs.djangoproject.com/en/stable/topics/class-based-views/generic-editing/#basic-forms

.. code-block:: python
	:caption: urls.py

	from formset.views import FormView

	from myproject.forms import RegisterPersonForm

	urlpatterns = [
	    ...
	    path('register_person', FormView.as_view(
	        form_class=RegisterPersonForm,
	        template_name='native-form.html',
	        success_url=success_url,
	    )),
	    ...
	]

When we navigate to the given URL, our form will be rendered by the class ``FormView``. Until here,
there is no difference on how Django renders a form. In case your project already defined a
proprietary class inheriting from FormView_ which can not be refactored, **django-formset** provides
a special mixin class named :class:`formset.views.FormViewMixin` to be inherited by that view.

The difference to a classic Django form appears when the view receives data sent by a POST request.
First of all, received data now is encoded as ``application/json``, instead of
``multipart/form-data``, as with standard form submissions. And secondly, the response of that
processed view is neither an HTTP redirect nor a HTML page, but just a data object, again encoded in
JSON. If that form validates successfully, that response object just contains the success URL with a
status code of 200. On the other hand, if the form does not validate, then that response object
contains the error messages of the fields submitting invalid data, indexed by their field names. The
status code of such a response then is 422, which stands for "`Unprocessable Entity`_". Having the
server respond with a status code indicating an error, makes it easier for the client to distinguish
between validated and invalid forms.

.. _Unprocessable Entity: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422

For invalid forms, the client's JavaScript code handling the web component ``<django-formset>``,
then fills the placeholders near the invalidated input fields with those error messages. It also
puts the HTML form element into an invalid state, so that it can not be re-submitted before editing.
The response on validated forms can be used to update the database or do other processing before
telling the browser where to go next. Instead of sending a HTTP redirect, the server now sends the
success URL wrapped in a JavaScript object. When receiving this response, the browser just loads the
page with that URL. This also prevents users to accidentally submit the form data twice, in case
they click on the browser's reload button.

A Django form using **django-formset** can be rendered using three different methods:

.. _native_form:

Using a Native Django Form
==========================

Working with a native Django form, presumably is the most frequent use case. Here we add an
instantiation of that form to the rendering context. Then that form instance is rendered using the
special template tag ``render_form``. The template responsible for rendering shall be written as:

.. code-block:: django

	{% load render_form from formsetify %}

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {% render_form form field_classes="mb-2" form_classes="rounded-xl" %}
	  <button type="button" click="submit -> proceed">Submit</button>
	</django-formset>

What we see here is that in addition to the form object, we pass a few CSS classes to the renderer.
These are named ``field_classes`` and ``form_classes``. Let's explain how we can use them to style
our form. When rendered, the above form will roughly turn into HTML such as:

.. code-block:: html

	<django-formset endpoint="/path/to/form-view" csrf-token="{{ csrf_token }}">
	  <form id="id_registerpersonform"></form>
	  <div class="rounded-xl dj-form">
	    <div class="dj-form-errors"><ul class="dj-errorlist"></ul></div>
	    <django-field-group class="mb-5 dj-required">
	      <label class="formset-label">First name:</label>
	      <input class="formset-text-input" form="id_registerpersonform" type="text" name="first_name" required="" pattern="^[A-Z][a-z -]+$">
	      <div role="alert" class="dj-field-errors">
	        <django-error-messages value_missing="This field is required." type_mismatch="A first name must start in upper case." pattern_mismatch="A first name must start in upper case." bad_input="Null characters are not allowed."></django-error-messages>
	        <ul class="dj-errorlist"><li class="dj-placeholder"></li></ul>
	      </div>
	    </django-field-group>
	    <!-- other form fields snipped away -->
	  </div>
	  <button type="button" click="submit -> proceed">Submit</button>
	</django-formset>

Compared to the way the native Django form renderer works, we see a few differences here: The most
obvious one is that input fields are not wrapped into their ``<form>``-element. Instead they refer
to the form they belong to by ID using the attribute ``form="id_registerpersonform"``. This is so
that forms can logically be nested into each other. Remember: It is invalid HTML to nest one
``<form>``-element into another one, but using that trick we can mimic that behviour.

Also note that each input field is wrapped into a ``<django-field-group>``-element. Even though this
tag may look like another web component, it just is a non-visual HTML element. Its purpose is to
group one or more input elements (in Django we name them widgets) belonging to one field together.
Remember that in HTML radios and multiple checkboxes have more than one input element, but in Django
they are considered as a single form field.

Moreover, CSS frameworks such as Bootstrap require to `group`_ the label and their input fields
into one HTML element, typically a ``<div>``. This is what the ``<django-field-group>`` does, in
addition to grouping the input elements. When adding the parameter ``field_classes="mb-5"`` to the
templatetag ``render_form``, that CSS class is added to each instance of the group, ie. it then is
rendered as ``<django-field-group class="mb-5">``.

.. _group: https://getbootstrap.com/docs/5.2/forms/form-control/

Another unknown HTML-element in the rendered form is ``<django-error-messages ...>``. This element
simply keeps all the potential error messages, in case a field validation fails on the client.
Remember that HTML5 introduced a bunch of `form controls`_ which are mapped to their Django
counterparts. If, for instance, the pattern of an input field of ``type="text"`` does not match the
specified regular expression, then the text from attribute ``type_mismatch`` is shown as an error
below that field.

.. _form controls: https://developer.mozilla.org/en-US/docs/Learn/Forms/Form_validation#using_built-in_form_validation,

.. _extended_form:

Using an Extended Django Form
=============================

One of the tasks the templatetag ``render_form`` must do, is to modify the signature of the given
form class. This is required, because the layout of the rendered HTML differs substantially from the
default by the Django form field renderers. Sometimes however, we may prefer to render the complete
form instance using its built-in ``__str__()``-method. In this use case, our form class has to
additionally inherit from :class:`formset.utils.FormMixin`. Such a form could for instance be
defined as:

.. code-block:: python

	from django.forms import forms, fields
	from formset.utils import FormMixin
	
	class RegisterPersonForm(FormMixin, forms.Form):
	    first_field = ...

The template required to render such a form then shall look like:

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {{ form }}
	  <button type="button" click="submit -> proceed">Submit</button>
	</django-formset>

Let's discuss these lines of HTML code step by step:

Since the JavaScript implementing web component ``<django-formset>`` communicates via Ajax with the
server, having a hidden field containing the CSRF-token doesn't make sense. Instead we pass that
token value as an attribute to the web component ``<django-formset>``. Since that value is available
in the rendering context, we always add it as ``<django-formset csrf-token="{{ csrf_token }}">``.

Having set up the form's template this way, allows us to render the form instance as a string. This
is what ``{{ form }}`` does. On the first sight, this may seem more cumbersome than the solution
shown before when :ref:`native_form`. In some situations however, it might be simpler to change the
signature of the form class in Python code, rather than changing the code in the template.

Another use case would be to have a form with more than one renderer, each configured differently.
We then can reuse a Django template but for instance render the form with different CSS classes.
If such a setup might make sense in your project, please check the section about :ref:`renderers`.


.. _field_by_field:

Rendering a Django Form Field-by-Field
======================================

In some occasions, we need an even more fine grained control over how fields shall be rendered. Here
we iterate over the form fields in our own loop or by accessing the fields by name. This way we can
render field by field and depending on the field's name or type, we could render it in different
manners. Let's have a look at such a template:

.. code-block:: django

	{% load formsetify %}
	...
	{% formsetify form %}
	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  <form id="{{ form.form_id }}"></form>
	  {% include "formset/non_field_errors.html" %}
	  {% for field in form %}
	    {% if field.is_hidden %}
	      {{ field }}
	    {% elif field.name == "my_special_field" %}
	      {% include "myproject/my_special_field.html" %}
	    {% else %}
	      {% include "formset/default/field_group.html" %}
	    {% endif %}
	  {% endfor %}
	  <button type="button" click="submit -> proceed">Submit</button>
	</django-formset>

Let's discuss these lines of HTML code step by step:

First we have to "formsetify" our form. This is required in order to change the signature of the
form class as described in the previous section. If the form instance already inherits from
:class:`formset.utils.FormMixin`, then this operation can be skipped.

We then iterate over all form fields. Here we must distinguish between hidden and visible input
fields. While the latter shall be wrapped inside a ``<django-field-group>`` each, the former shall
not. We can then further specialize our rendering logic, depending on which field we want to render.

Rendering a form field-by-field shall only be used as a last resort, because it inhibits the reuse
of the rendering templates. If fields have to be styled explicitly, for instance to place the input
field for the postal code on the same line as the input field for the "city", then a better approach
is to adopt the :ref:`renderers`.
