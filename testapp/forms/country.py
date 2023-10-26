from django.forms import fields, forms

from django_countries import countries

from formset.widgets import CountrySelectize, CountrySelectizeMultiple


class CountryForm(forms.Form):
    """
    How to use the Selectize widget with a CountryField.
    """
    single_country = fields.ChoiceField(
        label="Single Country",
        widget=CountrySelectize,
        choices=countries,
    )

    many_countries = fields.MultipleChoiceField(
        label="Multiple Countries",
        widget=CountrySelectizeMultiple(max_items=8),
        choices=countries,
        help_text="Select up to 8 countries",
    )
