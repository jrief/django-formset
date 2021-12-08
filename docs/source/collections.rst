.. _collections:

Form Collections
================

A very powerful feature of **django-formset** is the ability to create a collection of forms. In
Django we quite often create forms out of models and want to edit more than one of those forms on
the same page and post them in a single summission. By using a prefix on each Django Form, it is
possible to name the fields uniquely and on submission we can reassign the form data back to each
individual form. This however is limited to one nesting level and is quite cumbersome to handle.

In **django-formset** on the other side, we can create a Form Collection and explicitly add existing
forms as members of those Collection. It even is possible to add a Collection as member of another
Collection, in order to build a nested data structure.


Simple Collection
-----------------

We use this kind of collection, if we just want to group two or more forms together.

.. code-block:: python
	:caption: my_forms.py

	from formset.collection import FormCollection

	class MyFormCollection(FormCollection):
	    form1 = MyForm1()
	    form2 = MyForm2()

Collections must be rendered using the special View class :ref:`formset.views.FormCollectionView`:
The template used to render our Form Collection must ensure that the CSRF-Cookie is set; this is
done by accessing the CSRF token. Otherwise this View just behaves like an ordinary Form View
embedded in a **django-formset**.

.. code-block:: django
	:caption: my-collection.html

	<django-formset endpoint="{{ request.path }}">
	  {% with dummy=csrf_token.0 %}{% endwith %}
	  {{ form_collection }}
	</django-formset>

Finally add a route to the View:

.. code-block:: python
	:caption: urls.py

	from django.urls import path
	from formset.views import FormCollectionView
	from .my_forms import MyFormCollection

	urlpatterns = [
	    ...
	    path('contact', FormCollectionView.as_view(
	        template_name='my-collection.html'
	        collection_class=MyFormCollection,
	        success_url='/path/to/success',
	    )),
	    ...
	]


Nested Collection
-----------------

A Form Collection can not only contain other Django Forms, but also other Form Collections. This
means, that we can nest collections into each other up to currently 10 levels (this limit can be
increased if required).

Just as with simple collections, form data sent by the client is already structured using the same
hierarchie as the collection themselves.


Collections with Siblings
-------------------------

If a Form Collection contains one of the attributes ``min_siblings``, ``max_siblings`` or
``extra_siblings``, it is considered as a Collection with siblings. They then behave similar to
what we already know from Django Admin's StackedInlines or TabularInlines. The difference though
is, that we can now use this feature outside of the Admin, and that we can nest Collections with
siblings into each other.
