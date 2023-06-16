.. _intro:

============
Introduction
============

**django-formset** attempts to solve a problem, which occurs in almost every project using the
Django framework, specifically the way forms are handled.

Consider that we need a HTML form to collect. When using Django, this typically consists of creating
a form instance, a view instance, and a template rendering that form. The user then can enters data
into the fields of that form, which during submission are sent to the server for validation. If one
or more of those fields fail to validate, the form is re-rendered, annotating the fields containing
invalid data with a meaningful error message. The latter requires to fully reload the whole page.
From a usability point of view, this approach is far from being contemporary.

An often used apporach to improve the user experience is to combine a popular JavaScript framework
with `Django REST framework`_. Those JavaScript frameworks however impose their own way of getting
stuff done and usually don't share the same mindset with Django. For instance, in Django we
distinguish between `bound and unbound forms`_. This concept however doesn't make sense in
most JavaScript frameworks, and hence is not implemented. We therefore often must work around those
problems, which leads to cumbersome and un-`DRY`_ solutions.

.. _Django REST framework: https://www.django-rest-framework.org/
.. _bound and unbound forms: https://docs.djangoproject.com/en/stable/ref/forms/api/#bound-and-unbound-forms
.. _DRY: https://www.artima.com/articles/orthogonality-and-the-dry-principle

By using **django-formset**, we can use our well known Django form and view implementations and
gain a contemporary user experience. Legacy implementations can be ported easily, because one has
to apply only very few changes to the code base.

With **django-formset** we get a `web component`_ explicitly written to handle Django forms and
collections of forms (hence "formset"). This means that fields are pre-validated by the client,
giving immediate feedback on invalid field values. If the form's content then is sent to the server
and fails to validate there, those error messages are sent back to the client and show up nearby the
fields containing invalid data.

Giving feedback on a form which did not validate doesn't require a page reload anymore. The nice
thing about this approach is, that we **can reuse all of our current Django forms** (unaltered),
**can use our existing Django views** (with a small modification), but **neither have to add any
extra code nor endpoints to the URL routing** of our application.

.. _web component: https://developer.mozilla.org/en-US/docs/Web/Web_Components

.. _forms_as_logical_entities:

Use Forms as Logical Entities
=============================

The **django-formset** library separates the logical layer of a Django Form_ from their HTML entity
``<form>``.

What does that mean? In Django we can define a form as a group of fields with certain data-types.
Often these forms are derived from a Django model. On the client, this form then is rendered, can
be filled with data and submitted back to the server.

Typically there is one form per page, because the HTML standard does not allow you to submit more
than one form in one submission. With the introduction of FormSets_, Django provides a workaround
for this use-case. It however relies on prefixing each field from the forms making up a "FormSet"
with a unique identifier, so that those Django forms can be wrapped into one HTML
``<form>``-element. This makes the handling of multiple forms per page cumbersome and difficult to
understand.

By using **django-formset** on the other hand, each Django form corresponds to its own
self-contained ``<form>``-element. Inside each of these forms, all field names remain unmodified
and on submission, each form introduces its own namespace, so that the form data is submitted as a
dictionary of field-value-pairs. By doing so, we can even nest forms deeply, something currently
not possible with Django FormSets_.

.. _Form: https://docs.djangoproject.com/en/stable/topics/forms/
.. _FormSets: https://docs.djangoproject.com/en/stable/topics/forms/formsets/


.. rubric:: Example

Consider a simple form to ask a user for its first- and last name. Additionally we apply some
contraints on how these names have to be written. This form then is rendered and controlled by a
slightly modified Django view:

.. django-view:: person
	:view-function: PersonFormView.as_view(extra_context={'framework': 'tailwind'})
	:caption: Interacting with a form shows validation errors immediately.

	from django.core.exceptions import ValidationError
	from django.forms import forms, fields
	from formset.views import FormView 
	
	class PersonForm(forms.Form):
	    first_name = fields.RegexField(
	        r'^[A-Z][\-a-z ]+$',
	        label="First name",
	        error_messages={'invalid': "A first name must start in upper case."},
	        help_text="Must start in upper case followed by one or more lowercase characters.",
	    )

	    last_name = fields.CharField(
	        label="Last name",
	        min_length=2,
	        max_length=50,
	        help_text="Please enter at least two, but no more than 50 characters.",
	    )

	    def clean(self):
	        cd = self.cleaned_data
	        if cd.get("first_name", "").lower().startswith("john") \
	            and cd.get("last_name", "").lower().startswith("doe"):
	            raise ValidationError("John Doe is an undesirable person")
	        return cd

	class PersonFormView(FormView):
	    form_class = PersonForm
	    template_name = "form.html"
	    success_url = "/success"

It should be mentioned that this view must be rendered by wrapping the form inside the web component
``<django-formset>``. This web component then controls the client side functionality, such as
pre- and post-validation, submission, etc. The content of the two form fields is submitted to the
``endpoint="{{ request.path }}"``. Here this is the same Django view, which also is responsible for
rendering that form.

.. code-block:: django
	:caption: form.html

	{% load formsetify %}

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {% render_form form "tailwind" %}
	  <button type="button" df-click="submit">Submit</button>
	  <button type="button" df-click="reset">Reset to initial</button>
	</django-formset>

When looking at the rendered HTML code, there are a few things, which admittedly, may seem unusual
to us:

* The ``<form>`` tag neither contains a ``method`` nor an ``action`` attribute.
* The CSRF-token is not added to ``<django-formset>`` instead of a hidden input field.
* The "Submit" and "Reset" buttons are located outside of the ``<form>`` element.

.. note:: When using Django's internal formset_, the field names have to be prefixed with
	identifiers to distinguish their form affiliation. This is cumbersome and difficult to debug.
	By using **django-formset**, we can keep the field names, since our wrapper groups them into
	plain JavaScript objects.

In this example, the form is rendered by the special templatetag
``{% render_form form "tailwind" %}``. This templatetag can be parametrized to use the correct
style-guide for each of the supported CSS frameworks. It can also be used to pass in our own CSS
classes for labels, fields and field groups. More on this can be found in chapter
:ref:`native_form`.

It also is possible to render the form using the classic approach with mustaches, ie.
``{{ form }}``. Then however the form object can't be a native Django form. Instead it has to be
transformed using a special mixin class. More on this can be found in chapter :ref:`extended_form`.

Another approach is to render the form field-by-field. Here we gain full control over how each field
is rendered, since we render them individually. More on this can be found in chapter
:ref:`field_by_field`.


What are Web Components?
========================

According to `webcomponents.org`_, web components are a set of web platform APIs that allow you to
create new custom, reusable, encapsulated HTML tags to use in web pages and web apps. Custom
components and widgets built upon the web component standards, will work across modern browsers,
and can be used with any JavaScript library or framework that works with HTML.

Web components are based on existing web standards. Features to support web components are currently
being added to the HTML and DOM specs, letting web developers easily extend HTML with new elements
with encapsulated styling and custom behavior.

The JavaScript behind this component now handles the following functions:

* Client-side validation of our form fields using the constraints defined by our form.
* Serializes the data entered into our form fields.
* Handles the submission of that data, by sending it to the server's ``endpoint``.
* Receives server-side validation annotations and marks all fields containing incorrect data.
* On success, performs a different action, usually a redirect onto a success page.
* Handles various actions after the user clicked on the button. This is useful to make the button
  behave more interactively.

.. note:: Form data submitted by the web component ``<django-formset>`` is not send using the
	default enctype_ ``application/x-www-form-urlencoded``. Instead the data from all forms is
	packed together into a JavaScript object and submitted to the server using enctype
	``application/json``. This means that our Django view receiving the form data, must be able to
	process that data using a slightly modified handler.

.. _FormView: https://docs.djangoproject.com/en/stable/topics/class-based-views/generic-editing/
.. _XMLHttpRequest: https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest
.. _webcomponents.org: https://www.webcomponents.org/introduction
.. _formset: https://docs.djangoproject.com/en/stable/topics/forms/formsets/#formsets
.. _enctype: https://developer.mozilla.org/en-US/docs/Learn/Forms/Sending_and_retrieving_form_data#the_enctype_attribute


Annotation
==========

When designing this library, one of the main goals was to **keep the programming interface as near
as possible to the way Django handles forms, models and views**. It therefore is possible to reuse
existing Django form declarations with a minimal modification to existing code.

For details on why this project exists, please refer to section about the :ref:`history`.


License
=======

**django-formset** is licensed under the MIT public license. Please consult the the appropriate file
in the repository for details.


Contributing
============

Please read chapter :ref:`contributing` before opening issues or pull requests.
