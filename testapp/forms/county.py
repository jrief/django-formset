from django.forms import forms, models

from formset.widgets import DualSelector, Selectize, SelectizeMultiple

from testapp.models import County


class CountyForm(forms.Form):
    county = models.ModelChoiceField(
        label="County",
        queryset=County.objects.all(),
        widget=Selectize(
            search_lookup='county_name__icontains',
            group_field_name='state_name',
            placeholder="Select one county"
        ),
        required=True,
    )

    counties = models.ModelMultipleChoiceField(
        label="Counties",
        queryset=County.objects.all(),
        widget=DualSelector(
            search_lookup='county_name__icontains',
            group_field_name='state_name',
            #placeholder="Select one or more counties"
        ),
        required=True,
    )
