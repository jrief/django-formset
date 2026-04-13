.. _extending-formset:

=================================================
Extending django-formset with your own Components
=================================================

.. raw:: html

	 <script src="/static/testapp/js/formset-extensions.js"></script>

.. versionadded:: 2.3

Sometimes the widgets provided by **django-formset** are not sufficient for your needs. In this case
you can create your own combination of a Web Component and a Django widget, and use them in your
forms. A proven approach is to create a Web Component that mimics the behavior of an existing HTML
input element, and then use it as a drop-in replacement for the corresponding Django widget. This
way, you can leverage the existing form handling and validation logic of Django, while providing a
custom user interface.

We therefore create a Django widget that renders an HTML input field and optionally additional
elements. Since we want that input element to behave like a Web Component, we can use the
`is="my-component" <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/is>`_
syntax for that purpose.


Example
=======

Say that we want to create an input field that allows users to select a member of the Simpsons
family. A standard HTML select element would not be very visually appealing, so we want to create a
custom select area with icons representing the family members. The user can then click on a family
member to select it. Otherwse this select element should just behave like a normal select element,
meaning that the user does not have to fiddle around with the client-side implementation.

Let's start by creating a Django widget that renders an unnumbered list with items containg SVG
icons of the family members. Each item will have a data attribute with the name of the family
member.

.. django-view:: simpsons_widget
	:caption: widgets.py

	from django.forms.widgets import TextInput
	
	class SimpsonSelector(TextInput):
	    template_name = 'testapp/simpsons-selector.html'
	
	    def get_context(self, name, value, attrs):
	        context = super().get_context(name, value, attrs)
	        context['widget']['attrs']['is'] = 'simpsons-selector'
	        context['widget']['simpsons'] = [
	            ('abraham', "Abraham Simpson"),
	            ('bart', "Bart Simpson"),
	            ('burns', "Montgomery Burns"),
	            ('flanders', "Ned Flanders"),
	            ('lisa', "Lisa Simpson"),
	            ('maggie', "Maggie Simpson"),
	            ('marge', "Marge Simpson"),
	            ('santas', "Santas the Dog"),
	        ]
	        return context

This widget specifies a custom template that renders the select area. The context passed to the
template includes a list of tuples with the name and label of each family member. The input element
is rendered with the ``is="simpsons-selector"`` attribute, which allows us to target it with our Web
Component. This widget requires a special rendering template, which is shown here:

.. code-block:: django
	:caption: testapp/simpsons-selector.html

	{% load static %}
	{% include "django/forms/widgets/input.html" %}
	<ul>
	{% for member, label in widget.simpsons %}
		<li data-member="{{ member }}">
			<label>{{ label }}</label>
			<img src="{% static 'testapp/simpsons/'|add:member|add:'.svg' %}" />
		</li>
	{% endfor %}
	</ul>


We then can use this widget in a Django form using a standard ``CharField`` as a replacement 
for our select field.

.. django-view:: simpsons_form
	:caption: forms.py

	from django.forms.fields import CharField
	from django.forms.forms import Form

	class SimpsonsForm(Form):
	    member = CharField(
	        label="Member",
	        initial="bart",
	        widget=SimpsonSelector,
	    )

After attaching this form to a Django form view, we get a select area with icons for the family
members, with a much more appealing user intetrface than a normal select element. For developers
this widget behaves just like a normal text input field, so we can use it in our forms without
worrying about the client-side implementation.

.. django-view:: simpsons_view
	:view-function: SimpsonsView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'simpsons-result'}, form_kwargs={'auto_id': 'smp_id_%s'})
	:hide-code:

	from formset.views import FormView

	class SimpsonsView(FormView):
	    form_class = SimpsonsForm
	    template_name = "form.html"
	    success_url = "/success"


Client-side Implementation
==========================

In order to understand how the client-side implementation of this widget works, we can take a look
at the TypeScript code for the Web Component. A good practice is to separate the private
implementation named ``SimpsonsSelector`` from the the Web Component named ``SimpsonsInputElement``
which extends the HTML input element. This TypeScript class installs some event listeners to handle
user interactions and update the attributes of the list items used to render the select area. It
also updates the value of the input field when a family member is selected, and updates the visual
state.

.. literalinclude:: ../../testapp/assets/formset-extensions/SimpsonsSelector.ts
	:language: typescript
	:caption: SimpsonsSelector.ts

The next step is to register this extended ``HTMLInputElement`` as a Web Component using the
identifier ``simpsons-selector``. This is done in a separate file to keep the code organized and to
allow for multiple extenal Web Components in the same project. It also registers the Web Component
in the global scope of **django-formset**, so that it can be used inside our main component
``<django-formset>``.

.. literalinclude:: ../../testapp/assets/formset-extensions/formset-extensions.ts
	:language: typescript
	:caption: formset-extensions.ts

.. rubric:: Footnotes

Icons for the Simpson family are provided by `icons8.com <https://icons8.com/>`_.
