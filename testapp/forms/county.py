from django.forms import fields, forms, models

from formset.widgets import DualSelector, DualSortableSelector, Selectize, SelectizeMultiple

from testapp.models import County


class CountyForm(forms.Form):
    """
    Using ``<optgroup>`` in fields with Single and Multiple Choices
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
