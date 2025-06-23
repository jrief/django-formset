from django.forms import forms, models
from django_filters import FilterSet, ModelChoiceFilter
from formset.widgets import DualSelector, Selectize, SelectizeMultiple

from testapp.models import County, State


class CountyChoiceField(models.ModelChoiceField):
    def label_from_instance(self, obj):
        return {'label': obj.name, 'sublabel': obj.state.name, 'itemlabel': f"{obj.name} ({obj.state.code})"}


class StateForm(forms.Form):
    """
    Using adjacent fields for preselecting options
    """

    state = models.ModelChoiceField(
        label="State",
        queryset=State.objects.all(),
        widget=Selectize(
            search_lookup='name__icontains',
        ),
        initial=23,
    )
    county = CountyChoiceField(
        label="County",
        queryset=County.objects.select_related('state'),
        widget=Selectize(
            search_lookup=['name__icontains'],
            filter_by={'state': 'state_id'},
        ),
        initial=1293,
    )
    counties = models.ModelMultipleChoiceField(
        label="Counties",
        queryset=County.objects.select_related('state'),
        # widget=DualSelector(
        #     search_lookup=['name__icontains'],
        #     filter_by={'state': 'state__id'},
        # ),
        widget=SelectizeMultiple(
            search_lookup=['name__icontains'],
            filter_by={'state': 'state_id'},
        ),
        initial=[1247, 1288],
    )


class StatesForm(forms.Form):
    """
    Using adjacent fields for preselecting options
    """

    states = models.ModelMultipleChoiceField(
        label="States",
        queryset=State.objects.all(),
        widget=SelectizeMultiple(
            search_lookup='name__icontains',
        ),
        required=False,
        initial=[2, 47],
    )

    counties = models.ModelMultipleChoiceField(
        label="Counties",
        queryset=County.objects.all(),
        # widget=SelectizeMultiple(
        #     search_lookup=['name__icontains'],
        #     filter_by={'states': 'state__id'},
        # ),
        widget=DualSelector(
            search_lookup=['name__icontains'],
            filter_by={'states': 'state__id'},
        ),
        # initial=[3, 70, 2940],
    )


class StateFilterSet(FilterSet):
    state = ModelChoiceFilter(
        queryset=State.objects.all(),
    )

    @property
    def qs(self):
        parent_qs = super().qs
        if state := self.request.GET.get('filter-state'):
            return parent_qs.filter(state=state)
        return parent_qs


class StateFilteredForm(forms.Form):
    """
    Using adjacent fields for preselecting options
    """

    state = models.ModelChoiceField(
        label="State",
        queryset=State.objects.all(),
        widget=Selectize(
            search_lookup='name__icontains',
        ),
        initial=2,
    )
    county = models.ModelChoiceField(
        label="County",
        queryset=County.objects.all(),
        widget=Selectize(
            search_lookup=['name__icontains'],
            use_filter_set=StateFilterSet,
        ),
        initial=70,
    )
