from django.forms import models

from formset.widgets import DualSortableSelector

from testapp.models import PollModel


class ModelPollForm(models.ModelForm):
    class Meta:
        model = PollModel
        fields = '__all__'
        widgets = {
            'weighted_opinions': DualSortableSelector(search_lookup='label__icontains'),
        }
