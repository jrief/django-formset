from django.forms import models

from formset.collection import FormCollection
from formset.widgets import DualSortableSelector

from testapp.models import PollModel


class ModelPollForm(models.ModelForm):
    """
    Many-to-Many Field with specific mapping model
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
