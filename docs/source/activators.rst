.. _activators:

=============================
Activators and Button Widgets
=============================

In almost every form, there are buttons to submit or reset the fields content. In Django these
buttons must be added to the rendering templates as HTML elements. But if you think about it, a
button also is an input field, sometimes rendered as ``<button …>`` and sometimes as
``<input type="submit" …>``. Okay, the button's value is transient and it only is used to trigger
an action, such as submit or reset. But it still is an input field and it has a name, so why does
Django not provide a field type for it? 

This is where **django-formset** comes in. It provides a field type for buttons, named
:class:`formset.fields.Activator`. An ``Activator`` is a field that is used to trigger an action.
The default widget of an ``Activator`` field is, as one might expect, the
:class:`formset.widgets.Button` widget. An ``Activator`` can be used inside a Django ``Form`` or a
``FormCollection``. It then behaves very similar to a normal field. The main difference is that it
does not store any data. Instead, it waits for click events which then can be intercepted by other
components of the embedding ``django-formset``. This is an inversion of control. Instead of adding
an event listener to the button, which then performs some action, the interested component can add a
listener to the named ``Activator`` field. A dialog component for instance, can popup and disappear
by specifying any condition on buttons and other input fields.


Dialog 
