from django.forms import models

from formset.widgets import DualSortableSelector

from testapp.models import PollModel


class ModelPollForm(models.ModelForm):
    """
    Many-to-Many Field with specific mapping model
    ----------------------------------------------

    By default, Django handles the neccessary mapping model for a many-to-many relation by itself.
    In some situations one might want to add additional fields to that intermediate mapping model,
    for example to sort the selected options according to the users preferences. This is where the
    ``DualSortableSelector`` becomes useful. Its behavior is the same as for the ``DualSelector``,
    but options inside the right select box can be sorted by dragging. This ordering value then is
    stored in the field used for ordering.
    """

    class Meta:
        model = PollModel
        fields = '__all__'
        widgets = {
            'weighted_opinions': DualSortableSelector(search_lookup='label__icontains'),
        }
