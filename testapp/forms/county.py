from django.forms import fields, forms, models

from formset.widgets import DualSelector, DualSortableSelector, Selectize, SelectizeMultiple

from testapp.models import County, CountyUnnormalized


class CountyForm(forms.Form):
    """
    Using ``<optgroup>`` in fields with Single and Multiple Choices
    ---------------------------------------------------------------

    This form shows the usage of different choices fields when used with option groups. When
    selecting an option, it is sometimes desirable to first group those options according to
    another criteria. For instance, consider the 3143 counties in the US. When rendering them
    inside a select box, it would be rather unclear, which county belongs to which state. For this
    purpose, HTML provides the element ``<optgroup>``. Other than visually grouping options to
    select from, this element has no other effect.

    The **Classic Select** uses a Django ``ChoiceField`` together with the ``<select>`` widget as
    provided by  HTML. In Django this field can be used to show the usage of option groups
    (``<optgroup>``) by using a list of option tuples rather than a single string. This example
    is just used for reference.

    The **One County** uses a Django ``ChoiceField`` together with the ``Selectize`` widget as
    provided by **django-formset**. It shall be used when the number of choices exceeds 10 but
    also is well suited for less.

    The **Few Counties** field shows a ``ModelMultipleChoiceField`` using the ``SelectizeMultiple``
    widget configured to query from the associated model. It behaves similar to the ``Selectize``
    widget, but allows to choose one or more options. It shall be used if the maximum number of
    selectable options does not exceed more than say 10.

    The **Many Counties** field shows a ``ModelMultipleChoiceField`` using the ``DualSelector``
    widget configured to query from the associated Django Model. It shows two ``<select multiple>``
    elements, the left offering all available options and the right to keep the selected options.
    It shall be used if the number of selected options can exceed any number.

    The **Sortable Counties** field shows a ``ModelMultipleChoiceField`` using the
    ``DualSortableSelector`` widget. This is a variation of the ``DualSelector`` widget, but allows
    the user to sort the selected options before submission. It is well suited if the model
    used for the many-to-many relation also contains an ordering field. Note that it is impossible
    to move items out of one option group into another one.

    All four widgets ``Selectize, SelectizeMultiple``, ``DualSelector`` and ``DualSortableSelector``
    accepts these arguments:

     * ``search_lookup`` is the query part to filter for obects using the given queryset.
     * ``group_field_name`` in combination with option groups. This field is used to determine
       the group name.
    """

    classic_select = fields.ChoiceField(
        label="Classic Select",
        choices=[
            ("Theropods", [
                (1, "Tyrannosaurus"),
                (2, "Velociraptor"),
                (3, "Deinonychus"),
            ]),
            ("Sauropods", [
                (4, "Diplodocus"),
                (5, "Saltasaurus"),
                (6, "Apatosaurus"),
            ]),
        ],
    )

    one_county = models.ModelChoiceField(
        label="One County",
        queryset=County.objects.all(),
        widget=Selectize(
            search_lookup='name__icontains',
            group_field_name='state',
            placeholder="Select one county"
        ),
        required=True,
    )

    few_counties = models.ModelMultipleChoiceField(
        label="A few counties",
        queryset=County.objects.all(),
        widget=SelectizeMultiple(
            search_lookup='name__icontains',
            group_field_name='state',
            placeholder="Select one or more counties",
            max_items=20,
        ),
        required=True,
    )

    many_counties = models.ModelMultipleChoiceField(
        label="Many counties",
        queryset=County.objects.all(),
        widget=DualSelector(
            search_lookup='name__icontains',
            group_field_name='state',
            attrs={'size': 16},
        ),
        required=True,
    )

    sortable_counties = models.ModelMultipleChoiceField(
        label="Sortable counties",
        queryset=County.objects.all(),
        widget=DualSortableSelector(
            search_lookup='name__icontains',
            group_field_name='state',
            attrs={'size': 16},
        ),
        required=True,
    )
