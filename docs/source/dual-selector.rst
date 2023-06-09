.. _dual-selector:

====================
Dual Selector Widget
====================

This widget is usually used to control the mapping of a many-to-many relation. It consists of two
HTML elements of type ``<select multiple ...>`` placed side by side. The left part contains the
available options to select from, while the right part contains the already selected options.
Between those two select fields, six buttons are located. With the first four, one can move selected
options from left to right and vice versa. The last two buttons can be used to undo and/or redo a
missed assignment.


Features
========

The **DualSelector** widget is well known to Django admin users. There it is named
filter_horizontal_ which in my opinion is a somehow misleading name. In **django-formset**, this
widget however offers many more features than its Django's counterpart.

.. _filter_horizontal: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#django.contrib.admin.ModelAdmin.filter_horizontal


Asynchronous loading
--------------------

While assigning options, the Django model used to map from – can be huge and contain millions of
entries. In such a situation it would take a lot of resources to load all the options at once.
Therefore **django-formset** only loads a small portion of the available options. By scrolling to
the end of the select element, another chunk of options will be loaded from the server. So in case
the mapping table contains too many options, it is advisable to use the search field located on top
of the select element rather than scrolling down and waiting for the next chunk of options to be
loaded from the server.


Search Fields
-------------

On top of the left- and right select fields, there is one search input field each. While typing,
**django-formset** narrows down the number of available options. Here the left input field sends the
string typed into, to the server performing a remote lookup. Using the database to search for an
entry is much more efficient, rather than doing this using JavaScript inside the browser.


Undo and Redo Buttons
---------------------

While working with these kinds of widgets, it can easily happen to accidentally move the wrong
options. Sometimes the only solution to this is to reset the form and restart over again. By using
the **DualSelector** widget, one can use the undo and redo buttons to switch to the previous selections.


Usage
=====

The **DualSelector** can be used as a widget together with Django's choice fields of type
MultipleChoiceField_ or ModelMultipleChoiceField_. When declaring a form, it shall be added
as widget to the field's arguments

.. _MultipleChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#multiplechoicefield
.. _ModelMultipleChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.ModelMultipleChoiceField

.. django-view:: county_form

	from django.forms import fields, forms, models, widgets
	from formset.widgets import DualSelector
	from testapp.models import County

	class CountyForm(forms.Form):
	    county = models.ModelMultipleChoiceField(
	        queryset=County.objects.all(),
	        widget=DualSelector(search_lookup='name__icontains'),
	    )

If the queryset delivers more than 250 entries, the widget begins to load more entries as soon as
the user scrolls to the end of the select field. This also happens when typing into the left search
field. Therefore the view controlling forms with this field, must offer an endpoint to perform these
remote lookups to look for entries in the database. There is no need for a special endpoint, but the
view handling the form must inherit from :class:`formset.views.IncompleteSelectResponseMixin`.

Here we instantiate the widget :class:`formset.widgets.DualSelector` using the following arguments:

* ``search_lookup``: A Django `lookup expression`_. For choice fields with more than 50 options,
  this instructs the **django-formset**-library on how to look for other entries in the database. 
* ``group_field_name`` in combination with option groups. This field is used to determine the group
  name. See below.
* ``filter_by`` is a dictionary to filter options based on the value of other field(s). See below.

.. _lookup expression: https://docs.djangoproject.com/en/stable/ref/models/lookups/#lookup-reference

.. django-view:: county_view
	:view-function: CountyView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'county-result'}, form_kwargs={'auto_id': 'co_id_%s'})
	:hide-code:

	from formset.views import FormView 

	class CountyView(FormView):
	    form_class = CountyForm
	    template_name = "form.html"
	    success_url = "/success"


Comparison with SelectizeMultiple
---------------------------------

The **DualSelector** widget can be considered as the big sibling of the :ref:`selectize-multiple`.
Both widgets use the same lookup interface and hence can arbitrarily be swapped out against each
other, by changing the widget argument in the choice field. 

From a usability point of view, the **SelectizeMultiple** widget probably is easier to understand,
especially for inexperienced users. It is best suited when only a few options (say, less than 15)
shall be selectable together. And since it's much more compact, it shall be used if rendering space
is a concern.

On the other hand, the **DualSelector** widget shall be used whenever the users may select many
options out of a list of options. Therefore this widget does not limit the maximum number of
selectable options. It also might make sense to use this widget, whenever some kind of undo/redo
functionality is required.


Grouping Select Options
=======================  

Sometimes it may be desirable to group options the user may select from.

In the United States there are 3143 counties, many of them sharing the same name. When rendering
them inside a select box, it would be rather unclear, which county belongs to which state. For this
purpose, HTML provides the element ``<optgroup>``. Other than visually grouping options to select
from, this element has no other effect. Fortunately our ``DualSelector`` widget mimicks that feature
and so we can even group all counties by state by rewriting our form as:

.. django-view:: grouped_county_form

	class GroupedCountyForm(forms.Form):
	    county = models.ModelMultipleChoiceField(
	        label="County",
	        queryset=County.objects.all(),
	        widget=DualSelector(
	            search_lookup='name__icontains',
	            group_field_name='state',
	        ),
	        required=True,
	    )

.. django-view:: grouped_county_view
	:view-function: GroupedCountyView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'grouped-county-result'}, form_kwargs={'auto_id': 'gc_id_%s'})
	:hide-code:

	class GroupedCountyView(CountyView):
	    form_class = GroupedCountyForm

Since there are 3143 counties, many of them using the same name, it is confusing to show them in a
simple list of options. Instead we prefer to render them grouped by state. To achieve this, we have
to tell the field ``counties`` how to group them, by using the attribute ``group_field_name``. This
sets up the ``DualSelector``-widget to use the named field from the model specified by the queryset
for grouping.

When rendered, the ``<option>`` elements then are grouped inside ``<optgroup>``-s using the state's
name as their label:


Filtering Select Options
========================

As we have seen in the previous example, even grouping too many options might not be a user-friendly
solution. This is because the user has to type a word, at least partially. So the user already must
know what he’s looking for. This approach is not always practical. Many of the counties share the
same name. For instance, there are 34 counties named “Washington”, 26 named “Franklin” and 24 named
“Lincoln”. Using an auto-select field, would just show a long list of eponymous county names.

Since the user usually knows in which state the desired county is located, that selection field then
offers a reduced set of options, namely the counties of just that state. Therefore let's use
adjacent fields for preselecting options:

.. django-view:: filtered_county_form

	from formset.widgets import DualSelector, SelectizeMultiple
	from testapp.models import State

	class FilteredCountyForm(forms.Form):
	    state = models.ModelMultipleChoiceField(
	        label="State",
	        queryset=State.objects.all(),
	        widget=SelectizeMultiple(
	            search_lookup='name__icontains',
	        ),
	        required=False,
	        help_text="Select up to 5 states",
	    )

	    county = models.ModelMultipleChoiceField(
	        label="County",
	        queryset=County.objects.all(),
	        widget=DualSelector(
	            search_lookup=['name__icontains'],
	            filter_by={'state': 'state__id'},
	        ),
	        required=True,
	    )

This form shows the usage of two adjacent fields, where the first field's value is used to filter
the options for the next field. Here with the field **state**, the user can make a preselection of
one or more states. When the state is changed, the other field **county** gets filled with all
counties belonging to one of the selected states.

To enable this feature, widget ``DualSelector`` accepts the optional argument ``filter_by`` which
contains a dictionary such as ``{'state': 'state__id'}`` defining the lookup expression on the given
queryset. Here each key maps to an adjacent field and its value contains a lookup expression.

.. django-view:: filtered_county_view
	:view-function: FilteredCountyView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'filtered-county-result'}, form_kwargs={'auto_id': 'fc_id_%s'})
	:hide-code:

	class FilteredCountyView(CountyView):
	    form_class = FilteredCountyForm

Setting up forms using filters, can improve the user experience, because it reduces the available
options the user must choose from. This might be a more friendly alternative rather than using
option groups.


Sortable Dual Selector Widget
=============================

By default, Django handles the necessary mapping model for a many-to-many relation by itself.
In some situations one might want to add additional `fields to that intermediate mapping model`_,
for example to sort the selected opinions according to the user's preference. This is where the
special field ``SortableManyToManyField`` becomes useful.

.. _fields to that intermediate mapping model: https://docs.djangoproject.com/en/stable/topics/db/models/#intermediary-manytomany

As example, consider a poll application where a user can select one or more opinions. We therefore
need a many-to-many relationship between the poll entity and the chosen opinions, so we typically
would use a ``ManyToManyField`` to represent this relationship. However, users shall also be allowed
to weigh their chosen opinions. We can handle this by providing our own intermediate many-to-many
mapping model named ``WeightedOpinion``, which contains two foreign keys, one onto our
``PollModel``, the other onto our ``OpinionModel`` and additionally a number field to specify the
weighting .

.. code-block:: python

	from django.db import models
	from formset.fields import SortableManyToManyField
	
	class OpinionModel(models.Model):
	    label = models.CharField(
	        "Opinion",
	        max_length=50,
	    )

	class PollModel(models.Model):
	    weighted_opinions = SortableManyToManyField(
	        OpinionModel,
	        through='myapp.WeightedOpinion',
	    )
	
	class WeightedOpinion(models.Model):
	    poll = models.ForeignKey(
	        PollModel,
	        on_delete=models.CASCADE,
	    )
	
	    opinion = models.ForeignKey(
	        OpinionModel,
	        on_delete=models.CASCADE,
	    )
	
	    weight = models.BigIntegerField(
	        default=0,
	        db_index=True,
	    )
	
	    class Meta:
	        ordering = ['weight']

After instantiating a form out of our ``PollModel``, we replace the widget for handling the
many-to-many relation against a sortable variant named ``DualSortableSelector``. Its behavior is the
same as for the ``DualSelector`` widget as explained above, but options inside the right select box
can be sorted by dragging. This ordering value then is stored in the field named ``weight`` used for
ordering.

.. django-view:: poll_form
	:caption: forms.py

	from django.forms import models
	from formset.widgets import DualSortableSelector
	from testapp.models import PollModel

	class PollForm(models.ModelForm):
	    class Meta:
	        model = PollModel
	        fields = '__all__'
	        widgets = {
	            'weighted_opinions': DualSortableSelector(search_lookup='label__icontains'),
	        }

When rendered this widget looks like any other ``DualSelector``-widget, but options in its right
panel can be dragged to set their weight:

.. django-view:: poll_view
	:view-function: type('ArticleEditView', (SessionModelFormViewMixin, dual_selector.PollView), {}).as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'poll-result'}, form_kwargs={'auto_id': 'po_id_%s'})
	:caption: views.py

	from django.views.generic import UpdateView
	from formset.views import FormViewMixin, IncompleteSelectResponseMixin

	class PollView(IncompleteSelectResponseMixin, FormViewMixin, UpdateView):
	    model = PollModel
	    form_class = PollForm
	    template_name = 'form.html'
	    success_url = '/success'

.. note:: After submission, the opinion mapping is stored in the database together with the chosen
	sorting. Therefore after reloading this page, the same order of opinions will be shown in the
	right select panel.
