from django.forms import forms, models

from formset.widgets import DualSelector, Selectize, SelectizeMultiple

from testapp.models import County, State


class StateForm(forms.Form):
    """
    Using adjacent fields for preselecting options
    ----------------------------------------------

    This form shows the usage of two adjacent fields, where one field's value is used to filter
    the options for another field. Here with the field **state**, the user can make a preselection.
    When the state is changed, the other field **county** gets filled with all counties belonging
    to that state. Setting up a form using this functionality, can improve the user experience,
    because it reduces the available options to user must choose from. This can be a better
    alternative rather than using option groups.

    To make use of this feature, the widgets ``Selectize``, ``SelectizeMultiple`` and
    ``DualSelector`` accept the optional argument ``filter_by`` which must contain a dictionary
    where each key maps to an adjacent field and its value contains a lookup expression:

    .. code-block:: python

        from django.db import models
        from formset.widgets import Selectize
        from myapp.model import County, State

        class StateForm(forms.Form):
            state = models.ModelChoiceField(
                queryset=State.objects.all(),
            )

            county = models.ModelChoiceField(
                queryset=County.objects.all(),
                widget=Selectize(
                    search_lookup=['name__icontains'],
                    filter_by={'state': 'state__id'},
                ),
            )

    There is another example named "states" which can handle multiple options.
    """

    state = models.ModelChoiceField(
        label="State",
        queryset=State.objects.all(),
        widget=Selectize(
            search_lookup='name__icontains',
        ),
        required=False,
    )

    county = models.ModelChoiceField(
        label="County",
        queryset=County.objects.all(),
        widget=Selectize(
            search_lookup=['name__icontains'],
            filter_by={'state': 'state__id'},
        ),
    )


class StatesForm(forms.Form):
    """
    Using adjacent fields for preselecting options
    ----------------------------------------------

    This form shows the usage of two adjacent fields, where one field's value is used to filter
    the options for another field. Here with the field **states**, the user can make a preselection
    of one or more states. When the state is changed, the other field **counties** gets filled with
    all counties belonging to one of the selectd states. Setting up a form using this
    functionality, can improve the user experience, because it reduces the available options to
    user must choose from. This can be a better alternative rather than using option groups.

    To make use of this feature, the widgets ``Selectize``, ``SelectizeMultiple`` and
    ``DualSelector`` accept the optional argument ``filter_by`` which must contain a dictionary
    where each key maps to an adjacent field and its value contains a lookup expression:

    .. code-block:: python

        from django.db import models
        from formset.widgets import DualSelector, Selectize
        from myapp.model import County, State

        class StateForm(forms.Form):
            states = models.ModelMultipleChoiceField(
                queryset=State.objects.all(),
                widget=SelectizeMultiple(
                    search_lookup='name__icontains',
                ),
            )

            counties = models.ModelMultipleChoiceField(
                queryset=County.objects.all(),
                widget=DualSelector(
                    search_lookup=['name__icontains'],
                    filter_by={'state': 'state__id'},
                ),
            )

    There is another example named "state" which shows how to use this with a single
    option.
    """

    states = models.ModelMultipleChoiceField(
        label="States",
        queryset=State.objects.all(),
        widget=SelectizeMultiple(
            search_lookup='name__icontains',
        ),
        required=False,
    )

    counties = models.ModelMultipleChoiceField(
        label="Counties",
        queryset=County.objects.all(),
        widget=DualSelector(
            search_lookup=['name__icontains'],
            filter_by={'states': 'state__id'},
        ),
    )
