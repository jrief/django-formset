from django.forms import forms, models

from formset.widgets import Selectize

from testapp.models import County


class CountyForm(forms.Form):
    dynamic_opinion = models.ModelChoiceField(
        label="County",
        queryset=County.objects.all(),
        widget=Selectize(
            search_lookup='county_name__istartswith',
            group_value='state_name',
            placeholder="Select county"
        ),
        required=True,
    )

