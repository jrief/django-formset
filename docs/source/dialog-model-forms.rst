.. _dialog-model-forms:

==================
Dialog Model Forms
==================

.. versionadded:: 1.5

Together with :ref:`dialog-forms`, **django-formset** also offers dialog model forms. These forms
then are, as one might expect, bound to a Django model. They are very useful for a common use case:

A form with a select element to choose a model object as a foreign key. 

But if
that object yet does not exist, you may want to add it on the fly without leaving the current form.
This is a widespread pattern in many web applications, and **django-formset** provides a way to do
this.

Assume we we have a form for an issue tracker. This form has a field for the issue's assignee, which
is a foreign key to the user model. If that user does not exist, we would have to leave the form and
create it somewhere else, then come back to the current form and select the user from the dropdown
list. This is not very user-friendly, and we would like to be able to add a new user on the fly.


We want to be able to add a new user on the fly, without leaving
