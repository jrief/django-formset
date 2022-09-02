from django.forms import models

from formset.collection import FormCollection
from formset.widgets import DualSortableSelector

from testapp.models import PollModel


class ModelPollForm(models.ModelForm):
    """
    Many-to-Many Field with specific mapping model
    ----------------------------------------------

    By default, Django handles the neccessary mapping model for a many-to-many relation by itself.
    In some situations one might want to add additional fields to that intermediate mapping model,
    for example to sort the selected opinions according to the user's preference. This is where the
    special field ``SortableManyToManyField`` becomes useful.

    Say that we have a Django model containg a list of opinions and a model to keep the completed
    polls. Since more than one opinion can be assigned to each poll, we need a many-to-many
    relation between our ``PollModel`` and our ``OpinionModel``. But users shall also be allowed to
    weight their choosen opinions. We can handle this be providing our own many-to-many mapping
    model named ``WeightedOpinion``:

    .. code-block:: python

        from django.db import models
        from formset.fields import SortableManyToManyField
        from myapp.model import OpinionModel

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

    When we render our ``PollModel`` as form, **django-formset** replaces the widget for handling
    the many-to-many relation against a sortable variant named ``DualSortableSelector``. Its
    behavior is the same as for the ``DualSelector`` as explained in example 6, but options inside
    the right select box can be sorted by dragging. This ordering value then is stored in the field
    named ``weight`` used for ordering.
    """

    class Meta:
        model = PollModel
        fields = '__all__'
        widgets = {
            'weighted_opinions': DualSortableSelector(search_lookup='label__icontains'),
        }


class PollCollection(FormCollection):
    """
    Wrap a ModelForm into a FormCollection
    --------------------------------------

    Here we wrap an existing form, which inherits from `django.forms.models.ModelForm` class into a
    FormCollection. Apart from adding an extra nesting level in the submitted data, this does not
    have any side effects.

    Using this might be useful if you want to add a legend on top –, or a help text on the bottom
    of the rendered form, something which is only possible with collections.

    .. code-block:: python

        from formset.collection import FormCollection
        from myapp.forms import ModelPollForm

        class PollCollection(FormCollection):
            legend = "Sortable Many-to-Many Field"
            help_text = "Selected options on the right hand side can be sorted by dragging"
            poll = ModelPollForm()
    """
    legend = "Sortable Many-to-Many Field"
    help_text = "Selected options on the right hand side can be sorted by dragging"
    poll = ModelPollForm()
