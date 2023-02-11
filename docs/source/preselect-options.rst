.. _preselect-options:

=================
Preselect Options
=================

Sometimes there are thousands of options a user can choose from a select-field. Since this is not
practical using the built-in HTML ``<select>``-element, **django-formset** offers the alternative
:ref:`selectize`, with lookup- and lazy-loading functionality. But since the user has to type a
word, at least partially, he already must know what he's looking for. This approach is not always
practical. Consider an address form where a user must select a specific county. In the U.S., there
are 3143 of them, many of them sharing the same name. For instance, there are 34 counties named
"Washington", 26 named "Franklin" and 24 named "Lincoln". Using an auto-select field, would just
show a long list of eponymous county names.

To improve the user experience, we can add a field named "state" adjacent to the field named
"county". Since the user usually knows in which state the desired county is located, that selection
field then offers a reduced set of options, namely the counties of just that state. Consider these
models

.. code-block:: python
	:caption: models.py

	from django.db import models

	class State(models.Model):
	    name = models.CharField()
	
	class County(models.Model):
	    state = models.ForeignKey(
	        State,
	        on_delete=models.CASCADE,
	    )
	
	    name = models.CharField(
	        verbose_name="Name",
	        max_length=30,
	    )


To make use of this feature, the widgets ``Selectize``, ``SelectizeMultiple`` and ``DualSelector``
accept the optional argument ``filter_by`` which must contain a dictionary where each key maps to
an adjacent field and its value must contain a lookup expression:

.. code-block:: python
	:caption: forms.py

	from django.forms import forms, models
	from formset.widgets import Selectize
	from .models import County, State

	class StateForm(forms.Form):
	    state = fields.ChoiceField(
	        choices=lambda: [(state.id, state.name) for state in State.objects.all()],
	        required=False,
	    )
	
	    county = models.ModelChoiceField(
	        queryset=County.objects.all(),
	        widget=Selectize(
	            search_lookup=['name__icontains'],
	            filter_by={'state': 'state__id'},
	        ),
	    )

Here, by selecting a state using the choice field **state**, the user can make a preselection.
When the state is changed, the other field **county** gets filled with all counties belonging
to that state. This filtering is done using the lookup expression ``state_id`` on the given
queryset.

Setting up a form using this functionality can improve the user experience, as it reduces the
available options the user must choose from. This can be a better alternative rather than using
option groups. This feature also works for the special select widgets accepting multiple options,
such as ``SelectizeMultiple`` and ``DualSelector``. 
