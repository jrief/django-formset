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

    The **Historic Regions** uses a Django ``ChoiceField`` together with the ``<select>`` widget
    as provided by  HTML. In Django this field can be used to show the usage of option groups
    (``<optgroup>``) by using a list of option tuples rather than a single string. This example
    is just used for reference to show how options groups would look like without modern widgets.
    Even with only 34 options, this widget becomes quite unhandy.

    The **One County** uses a Django ``ChoiceField`` together with the ``Selectize`` widget as
    provided by **django-formset**. It shall be used when the number of choices exceeds 10 but
    also is well suited for less. Here the limit is set to 15 items, but this value can be changed.

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
     * ``filter_by`` is a dictionary to filter options based on the value of other field(s).
    """

    historic_regions = fields.ChoiceField(
        label="Historic Regions",
        choices=[
            ('', "––––––––––"),
            ("New England", [
                (1, "Acadia"),
                (2, "Equivalent Lands"),
                (3, "King's College Tract"),
                (4, "Provinces of Maine"),
                (5, "Massachusetts Bay"),
                (6, "New Hampshire"),
                (7, "New Haven"),
                (8, "Plymouth"),
                (9, "Saybrook"),
                (10, "Wessagusset"),
            ]),
            ("Mid-Atlantic", [
                (11, "Granville"),
                (12, "East Jersey"),
                (13, "West Jersey"),
                (14, "New Netherland"),
                (15, "New Sweden"),
            ]),
            ("Southern", [
                (16, "Province of Carolina"),
                (17, "Fort Caroline"),
                (18, "Charlesfort"),
                (19, "La Florida"),
                (20, "Jamestown"),
                (21, "Fairfax Grant"),
                (22, "Roanoke"),
                (23, "Stuarts"),
            ]),
            ("Interior", [
                (24, "West Augusta"),
                (25, "Illinois Country"),
                (26, "Indiana"),
                (27, "Indian Reserve"),
                (28, "Ohio"),
                (29, "Quebec"),
            ]),
            ("Far West", [
                (30, "La Louisiane"),
                (31, "Luisiana"),
                (32, "Tejas"),
                (33, "Santa Fe"),
                (34, "Las Californias"),
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
            max_items=15,
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
        # initial=[3000, 498, 96, 95, 69, 14, 415, 10, 6],
    )
