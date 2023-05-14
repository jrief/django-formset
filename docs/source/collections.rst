.. _collections:

================
Form Collections
================

A very powerful feature of **django-formset** is the ability to create a collection of forms. In
Django we quite often create forms out of models and want to edit more than one of those forms on
the same page and post them in a single submission. By using a prefix on each Django Form, it is
possible to name the fields uniquely and on submission we can reassign the form data back to each
individual form. This however is limited to one nesting level and in order to add extra forms
dynamically, we must create our own JavaScript function, which is not provided by the Django
framework.

In **django-formset** on the other hand, we can create a form collection and explicitly add existing
forms as members of those collections. It's even possible to add a collection as a member of another
collection, in order to build a pseudo nested [#1]_ structure of forms.

The interface for classes inheriting from :class:`formset.collection.FormCollection` is
intentionally very similar to that of a Django ``Form`` class. It can be filled with a ``data``
dictionary as received by a POST request. It also can be initialized with an ``initial`` dictionary.
Since collections can be nested, the ``data`` and ``initial`` dictionaries must contain the same
shape as the nested structure.

Furthermore, a ``FormCollection`` offers a ``clean()``-method, which returns a cleaned representation
of the data provided by a client's submission.


Simple Collection
=================

We use this kind of collection, if we just want to group forms together. Assume we build an
apparatus which uses a chemical and an electrical sensor. Both sensors provide their own Django
library with a form each. Each form validates the user input according to the constraints given  
by their physicochemical characteristics.

In a typical Django application we now would have to create one form and combine the fields from
both libraries, then create a validation method (typically `clean()`) integrating the contraints for
both of them. But in order to keep our software modular, we would like to leave those independent
forms as separate entities.

Here is a very simplified example showing how we can achive this:

.. django-view:: simple
	:view-function: ApparatusView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'simple-collection-result'})
	:caption: apparatus.py

	from django.forms import fields, forms
	from formset.collection import FormCollection
	from formset.renderers.bootstrap import FormRenderer
	from formset.views import FormCollectionView

	class ChemistryForm(forms.Form):
	    ph_value = fields.FloatField(
	        label="pH value",
	        initial=7.0,
	        min_value=0.0,
	        max_value=14.0,
	        step_size=0.1,
	    )

	class ElectricityForm(forms.Form):
	    resistance = fields.IntegerField(
	        label="Resistance in Ω",
	        min_value=1,
	        initial=100,
	    )

	class ApparatusCollection(FormCollection):
	    default_renderer = FormRenderer(field_css_classes='mb-3')
	    substance = ChemistryForm()
	    conductivity = ElectricityForm()

	class ApparatusView(FormCollectionView):
	    collection_class = ApparatusCollection
	    template_name = "form-collection.html"
	    success_url = "/success"

When submitting this collection, the form data from both forms, ``substance`` and ``conductivity``
is already prevalidated by the browser using the given form constraints. On submission, the data is
handled separately and the collection then dispatches each of the sub-dicts to the appropriate form.

.. note::
	The class ``ApparatusCollection`` uses the Bootstrap ``FormRenderer``. This is required,
	otherwise the forms would be rendered unstyled. More on that later. 

Collections must be rendered using the special view class :class:`formset.views.FormCollectionView`.
The template used to render this ``ApparatusCollection`` must ensure that the CSRF-token is set;
this is done by passing that CSRF token value as attribute to the web component
``<django-formset …>``. Otherwise this view behaves just like any ordinary Django ``FormView``
embedded in a **django-formset**.

.. code-block:: django
	:caption: form-collection.html

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {{ form_collection }}
	</django-formset>

Finally add a route to the view as you always do.

.. code-block:: python
	:caption: urls.py

	from django.urls import path
	from .apparatus import ApparatusView

	urlpatterns = [
	    ...
	    path('apparatus', ApparatusView.as_view()),
	    ...
	]


.. _nested-collection:

Nested Collection
=================

A Form Collection can not only contain other Django Forms, but also other Form Collections. This
means that we can nest collections into each other up to currently 10 levels (this limit can be
increased if required).

Say that our apparatus is part of a machine with a control panel. That control panel has a switch
to turn the power on or off.

.. django-view:: nested
	:view-function: MachineView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'nested-collection-result'}, collection_kwargs={'renderer': FormRenderer(field_css_classes='mb-3')})
	:caption: machine.py

	class ControlPanelForm(forms.Form):
	    power = fields.BooleanField(label="Power", required=False)

	class MachineCollection(FormCollection):
	    control = ControlPanelForm()
	    apparatus = ApparatusCollection()

	class MachineView(FormCollectionView):
	    collection_class = MachineCollection
	    template_name = "form-collection.html"
	    success_url = "/success"

Just as with simple collections, form data sent from the browser is already structured using the
same hierarchy as the collections themselves.


.. _collections-with-siblings:

Collections with Siblings
=========================

We have seen that we can nest single collections, but we can also instantiate them multiple times.

If a class inheriting from :class:`formset.collection.FormCollection` contains one of the attributes
``min_siblings``, ``max_siblings`` or ``extra_siblings``, it is considered as a *collection with
siblings*. They then behave similar to what we already know as Django's `InlineModelAdmin objects`_.
The difference though is, that we can use this feature outside of the Django-Admin, and moreover,
that we can nest collections into each other recursively.

.. _InlineModelAdmin objects: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#inlinemodeladmin-objects

Whenever a collection is declared to have siblings, its member collections are rendered from zero,
once or multiple times. For each collection with siblings there is one "Add" button, and for each of
the child collections there is a "Remove" button. To avoid having too many "Remove" buttons, they
are invisible by default and only become visible when moving the cursor over that collection.

Since form fields in nested collections with siblings can quickly become confusing, those
collections offer a variety of attributes to organize them for better visibility:

.. rubric:: Legend

Just as HTML-elements of type ``<fieldset>`` can contain a legend, a form collection may optionally
also contain a ``<legend>…</legend>``-element. It is placed on top of the collection and shall be
specified as attribute ``legend = "…"`` inside classes inheriting from
:class:`formset.collection.FormCollection`, or as a parameter when initializing the collection.


.. rubric:: Help Text

A form collection may optionally render a ``<div>…</div>``- or ``<p>…</p>``-element (depending on
the best practices of the CSS framework) at its end, containing a help text string. It shall be
specified as attribute ``help_text = "…"`` inside classes inheriting from
:class:`formset.collection.FormCollection`, or as a parameter when initializing the collection.


.. rubric:: Label for "Add" button

The parameter ``add_label`` shall contain a human readable string, telling the user what kind of
collection to add as a sibling. If unset, the "Add" button just contains the **+** symbol.


.. rubric:: Minimum Number of Siblings

The parameter ``min_siblings`` tells us how many collections the parent collection must contain as
minimum. If unset, it defaults to 1.


.. rubric:: Maximum Number of Siblings

The parameter ``max_siblings`` tells us how many collections the parent collection may contain as
maximum. If unset, there is no upper limit.


.. rubric:: Extra Siblings

The parameter ``extra_siblings`` tells us how many empty collections the parent collection starts
with. If unset, it defaults to 0, which means that the user must explicitly add a new sibling by
clicking on the "Add" button below the last sibling.

Say that our apparatus shall take a measurement from time to time and we want to keep track when
that happend. We thererfore add a form with a timestamp field and add this form to a collection
with siblings.

.. django-view:: with_siblings
	:view-function: ApparatusTimestampView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'atc-result'}, collection_kwargs={'auto_id': 'atc_id_%s', 'initial': {'logs': [{'log': {'timestamp': '2023-03-31T16:55'}}]}, 'renderer': FormRenderer(field_css_classes='mb-3')})

	from django.utils.timezone import now
	from formset.widgets import DateTimeLocalInput

	class LogForm(forms.Form):
	    timestamp = fields.DateTimeField(
	        label="Timestamp",
	        initial=now,
	        widget=DateTimeLocalInput,
	    )

	class LogCollection(FormCollection):
	    min_siblings = 1
	    add_label = "Add new Timestamp"
	    log = LogForm()

	class ApparatusTimestampCollection(FormCollection):
	    substance = ChemistryForm()
	    conductivity = ElectricityForm()
	    logs = LogCollection()

	class ApparatusTimestampView(FormCollectionView):
	    collection_class = ApparatusTimestampCollection
	    template_name = "form-collection.html"
	    success_url = "/success"

Note that a collection with siblings behaves differently, when deleting a child collection. If that
child collection was initialized and thus loaded from the server, then it is rendered with a
streaked background pattern, which signalizes to be removed on submission.

If on the other side that child collection was just added by clicking on the "Add" button below the
last sibling, then that collection will be deleted immediately. This is because for initialized
collections, while submitting we have to keep a placeholder in order to tell the server how to
change the underlying model. This can be tried out in the above example. The first form named
"Timestamp" is shadowed when deleted. Forms which just have been added are removed immediatly. 

.. rubric:: Ignore collections marked for removal

Adding the boolean parameter ``ignore_marked_for_removal`` to a class inheriting from
:class:`formset.collection.FormCollection` tells the ``clean()``-method how to proceed with
collections marked for removal. If unset or ``False`` (the default), such collections contain the
special key value pair ``'_marked_for_removal_': True`` inside their returned ``cleaned_data``
structure. This information shall be used, when the backend has to locate the proper object in a
database in order to delete it. If ``ignore_marked_for_removal = True``, then collections marked for
removal do not even appear inside that ``cleaned_data`` structure returned by the
``clean()``-method. The latter may be useful, if the form's payload shall be stored inside a
non-relational database or a JSON field.


Sortable Collections with Siblings
==================================

Whenever we work with a list of form collections, it might make sense to reorder the given entities.
This allows the user to sort the siblings of a collection. To achieve this, either add
``is_sortable = True`` when declaring the collection class, or instantiate the collection class
by passing ``is_sortable=True`` to its constructor.

Form collections declared to by sortable, render a small drag area on their top right corner. By
dragging that handle, the user can reorder the chosen collections. On form submission, that new
order is reflected inside the list of transferred fields. When using a sortable collection to edit a 
(query-)set of models, it therefore is mandatory to include the primary key of each object as a
hidden input field. Otherwise it will not be possible to reorder those objects afterwards in the
database.

.. django-view:: sortable_siblings
	:view-function: AddressBookView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'ab-result'}, collection_kwargs={'renderer': FormRenderer(field_css_classes='mb-3')})

	class PersonForm(forms.Form):
	    full_name = fields.CharField(
	        label="Full name",
	        min_length=3,
	        max_length=50,
	    )

	class PhoneNumberForm(forms.Form):
	    phone_number = fields.RegexField(
	        r'^[01+][ 0-9.\-]+$',
	        label="Phone Number",
	        min_length=2,
	        max_length=20,
	        help_text="Valid phone numbers start with + or 0 followed by digits and spaces",
	    )

	class PhoneNumberCollection(FormCollection):
	    legend = "List of Phone Numbers"
	    add_label = "Add new Phone Number"
	    min_siblings = 1
	    max_siblings = 5
	    extra_siblings = 1
	    is_sortable = True
	
	    number = PhoneNumberForm()

	class ContactCollection(FormCollection):
	    legend = "Contact"
	    person = PersonForm()
	    numbers = PhoneNumberCollection()

	class AddressBookView(FormCollectionView):
	    collection_class = ContactCollection
	    template_name = "form-collection.html"
	    success_url = "/success"

One must note that it is only possible to reorder collections inside its direct parent collection.
It therefore is not possible to drag a sub collection into another collection.


.. rubric:: Footnotes

.. [#1] HTML does not allow nesting ``<form>``-elements. However, we can wrap those ``<form>``-s
	into our own web components which themselves are nested and hence mimic that behavior. 
