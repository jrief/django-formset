from django.forms import fields, forms, models, widgets

from formset.widgets import Selectize, DualSelector, SelectizeMultiple

from testapp.models import OpinionModel


class OpinionForm(forms.Form):
    """
    Fields with Single and Multiple Choices
    ---------------------------------------

    This form shows the usage of different choices fields.

    The **Classic Select** uses a Django ``ChoiceField`` using the ``<select>`` widget as provided
    by  HTML. This is the default and shall only be used for fields with a very few choices, say
    less than 10. It can't be styled through CSS.

    The **Static Opinion** uses a Django ``ChoiceField`` using the new ``Selectize`` widget with a
    fixed set of choices. It shall be used when the number of choices exceeds 10 but also is well
    suited for less.

    The **Dynamic Opinion** field shows a ``ModelChoiceField`` using the ``Selectize`` widget
    configured to query from the associated Django Model. While typing into this field, the number
    of choices narrows down to those matching the search query string.

    The **Few Opinions** field shows a ``ModelMultipleChoiceField`` using the ``SelectizeMultiple``
    widget configured to query from the associated model. It behaves similar to the ``Selectize``
    widget, but allows to choose one or more options. It shall be used if the maximum number of
    selectable options does not exceed more than say 10.

    The **Many Opinions** field shows a ``ModelMultipleChoiceField`` using the ``DualSelector``
    widget configured to query from the associated Django Model. It shows two ``<select multiple>``
    elements, the left offering all available options and the right to keep the selected options.
    It shall be used if the number of selected options can exceed any number.

    The **Annotation** field is just added as a reference to compare the feedback from the
    ``Selectize`` widget with a standard input field.
    """

    choice = fields.ChoiceField(
        label="Classic Select",
        choices=[
            (None, "Commit yourself"),
            (1, "In favor"),
            (2, "Against"),
            (3, "Don't know"),
        ],
    )

    static_opinion = fields.ChoiceField(
        label="Static Opinion",
        choices=lambda: OpinionModel.objects.filter(tenant=1).values_list('id', 'label')[:99],
        widget=Selectize(placeholder="Select from static opinion"),
    )

    dynamic_opinion = models.ModelChoiceField(
        label="Dynamic Opinion",
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=Selectize(
            search_lookup='label__icontains',
            placeholder="Select from dynamic opinion",
        ),
        required=True,
    )

    few_opinions = models.ModelMultipleChoiceField(
        label="Few Opinions",
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=SelectizeMultiple(
            search_lookup='label__icontains',
            placeholder="Select up to 9 opinions",
            max_items=9,
        ),
    )

    many_opinions = models.ModelMultipleChoiceField(
        label="Many Opinions",
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=DualSelector(
            search_lookup='label__icontains',
            attrs={'size': 8},
        ),
        initial=range(10, 1200, 57),
    )

    annotation = fields.CharField(
        label="Annotation",
        widget=widgets.TextInput(attrs={'placeholder': "Start typing ..."}),
        required=False,
        help_text="I have to say something",
    )


sample_opinion_data = {
    'choice': 2,
    'static_opinion': lambda: OpinionModel.objects.filter(tenant=1)[6],
    'dynamic_opinion': lambda: OpinionModel.objects.filter(tenant=1)[9],
    'annotation': "Lorem ipsum dolor est",
}
