.. _styling:

Styling Forms with django-formset
=================================

**django-formset** ships with renderers, each one specialzed to render all possible Django form
widgets for different CSS frameworks.

* Input fields of type text, with validation for minimum and maximun input length.
* Input fields of type text with pattern matching.
* Input fields of type number, with validation for its input range.
* Input fields of type date. This currently uses the default date widget from the browser, but
  future versions will offer their own native date widget.
* Checkboxes for a single input. They can be styled reversing label and input field.
* Radio buttons with support for option groups. They can be arranged to align horizontally.
* Multiple checkboxes with support for option groups. They can be arranged to align horizontally.
* Select boxes with predefined options.
* Select boxes with autocomplete behaviour.
* Textarea fields.
* File upload fields with asynchronous upload and drag & drop support. 

Currently not supported widgets:

* Multiple selects with source and target boxes.
* Geospacial fields.


Default Styling
---------------

The default **django-formset** styling intentionally renders all the fields as the browser would by
default. This admiditly looks very rough and we only use it, if we want to style every aspect of our
web site. This requires to write the CSS ourselfs. If we use one of the known CSS frameworks, then
instead we will proceed with one of the specialized renderes. The concept for rendering a form
remains to same, independently of the CSS framework.

Say we have a typical Django form

.. code-block:: python

	from django.forms import forms, fields
	
	class RegisterPersonForm(forms.Form):
	    first_name = fields.RegexField(
	        r'^[A-Z][a-z -]+$',
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

	    gender = fields.ChoiceField(
	        label="Gender",
	        choices=[('m', "Male"), ('f', "Female")],
	        widget=widgets.RadioSelect,
	        error_messages={'invalid_choice': "Please select your gender."},
	    )

When rendered using the view class :class:`formset.views.FormView` together with this template 

.. code-block:: django

	{% load formsetify %}

	<django-formset endpoint="{{ request.path }}">
	  {% render_form form %}
	  <button type="button" click="submit -> proceed">Submit</button>
	</django-formset>

that form displays two text input fields, one for the person's first- and its last name. Here we
declared two constraints on the first two fields: The first name must start in upper case and
contain at least one additional character in lower case, while the last name must consist from at
least two, but no more than 50 characters. Additionally the user has to choose his gender using
two radio input fields and a mandatory checkbox input to accept the terms and conditions.

.. image:: _static/unstyled-form.png
  :width: 560
  :alt: Unstyled Form

Styling this form now is up you. Use this as a starting point, if you edit the CSS of your project
anyway. There are a few HTML tags and CSS classes, which might help styling:

* ``django-fieldgroup > label``: The label right above the input element. 
* ``django-fieldgroup input[type="..."]``: The input element. Use the correct ``type`` here.
* ``django-fieldgroup > .dj-help-text``: Some optional helptext below the input field(s).
* ``django-fieldgroup > ul.dj-errorlist li.dj-placeholder``: This list-element usually is empty.
  If filled, it contains the validation error message. 

Always remember to add

.. code-block:: django

	<script type="module" src="{% static 'formset/js/django-formset.js' %}"></script>

anywhere inside the ``<head>``-element of the page.


Bootstrap
---------

Bootstrap is probably the most popular CSS framework nowadays, and **django-formset** offers a
renderer, which renders all its input fields as proposed by the `Boostrap's form usage guide`_.

.. _Boostrap's form usage guide: https://getbootstrap.com/docs/5.1/forms/overview/

In the template from above, we simply replace the templatetag against

.. code-block:: django

	{% render_form form "bootstrap" field_classes="mb-2" %}

and get a much nicer looking form

.. image:: _static/bootstrap-form.png
  :width: 560
  :alt: Bootstrap Form

Compared to the unstyled form shown in the previous section, we notice that the radio fields
are inlined and that the checkbox is positioned before its label. This behaviour is intended.

According to the Bootstrap's usage guide, checkboxes shall be placed on the left side of their
label. Django can't handle this by itself, because it does not distinguish between checkbox input
fields and other types of fields.


Inlining Form Fields
....................

By using slightly different parameters, a form can be rendered with labels and input fields side
by side, rather than beneeth each other. This can be achieved by applying these CSS classes
to the templatetag

.. code-block:: django

	<django-formset endpoint="{{ request.path }}">
	  {% render_form form "bootstrap" field_classes="row mb-3" label_classes="col-sm-3" control_classes="col-sm-9" %}
	  <div class="offset-sm-3">
	    <button type="button" click="submit -> proceed">Submit</button>
	  </div>
	</django-formset>

and we get a form rendered as

.. image:: _static/styling-bootstrap-inline.png
  :width: 560
  :alt: Bootstrap Form


Inlining Radio Buttons and Multiple Checkboxes
..............................................

In **django-formset**, radio buttons and multiple checkboxes can be inlined, if there are only a
few of them. The default threshold is 4 and can be modified with the parameter
``max_options_per_line``. It can be passed in through the templatetag

.. code-block:: django

	  {% render_form form "bootstrap" max_options_per_line=3 %}


Bulma
-----

Bulma is another popular CSS framework nowadays, and **django-formset** offers a renderer, which
renders all its input fields as proposed by `Bulma's form control usage guide`_.

.. _Bulma's form control usage guide: https://bulma.io/documentation/form/general/
