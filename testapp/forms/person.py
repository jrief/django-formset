from django.core.exceptions import ValidationError
from django.forms import fields, forms, models, widgets

from formset.widgets import Selectize, SelectizeMultiple, UploadedFileInput, DualSelector

from testapp.models import PersonModel


class SimplePersonForm(forms.Form):
    last_name = fields.CharField(
        label="Last name",
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
    )

    first_name = fields.RegexField(
        r'^[A-Z][a-z -]*$',
        label="First name",
        error_messages={'invalid': "A first name must start in upper case."},
        help_text="Must start in upper case followed by one or more lowercase characters.",
        max_length=50,
    )


class PersonForm(SimplePersonForm):
    def clean(self):
        cd = super().clean()
        if cd['first_name'].lower().startswith("john") and cd['last_name'].lower().startswith("doe"):
            raise ValidationError(f"{cd['first_name']} {cd['last_name']} is persona non grata here!")
        return cd


sample_person_data = {
    'first_name': "John",
    'last_name': "Doe",
}


class ModelPersonForm(models.ModelForm):
    class Meta:
        model = PersonModel
        fields = '__all__'
        widgets = {
            'avatar': UploadedFileInput,
            'gender': widgets.RadioSelect,
            'opinion': Selectize(search_lookup='label__icontains'),
            'opinions': SelectizeMultiple(search_lookup='label__icontains', max_items=15),
            #'opinions': DualSelector(search_lookup='label__icontains'),
        }
