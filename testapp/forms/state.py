from django.forms import forms, models

from formset.widgets import Selectize

from testapp.models import County, State


class StateForm(forms.Form):

    state = models.ModelChoiceField(
        label="State",
        queryset=State.objects.all(),
        widget=Selectize(
            search_lookup='name__icontains',
        ),
        #initial=5,
    )

    county = models.ModelChoiceField(
        label="County",
        queryset=County.objects.all(),
        widget=Selectize(
            search_lookup=['name__icontains'],
            filter_by={'state': 'id'},
        ),
    )
