.. _fieldsets:

Fieldsets
=========

In HTML the ``<form>``-element is just a data-abstraction layer. It has no display properties and is
not intended to be styled or anotated. Its purpose is to group one or more input fields, in order to
submit them to the server altogether.

On the other side, we might want to visually group those input fields and optionally add a legend
or style the border. For this purpose the HTML standard defines the tag ``<fieldset>``. Django
itself does not offer any abstraction for this HTML tag. If one wants to use it, this has to be done
on the template level when rendering the form.

For this purpose, **django-formset** introduces a Python class to handle the Fieldset element. From
a technical point of view, a fieldset behaves exactly like a single form and in HTML it always is
wrapped inside a ``<form>``-element. If we want to use more than one fieldset, then we have to group
them using :ref:`collections`, just as we would do with normal forms.

The purpose of using fieldsets is not only to add a visual layer and legend to a form, but to also
hide or disable the whole fieldset using :ref:`conditionals`.


Example
-------

