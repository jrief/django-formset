from django.core.exceptions import ValidationError
from django.forms import fields, forms, widgets


class QuestionnaireForm(forms.Form):
    first_name = fields.RegexField(
        r'^[A-Z][a-z -]+$',
        label="First name",
        error_messages={'invalid': "A first name must start in upper case."},
        help_text="Must start in upper case followed by one or more lowercase characters.",
    )

    last_name = fields.CharField(
        label="Last name",
        min_length=2,
        max_length=50,
        help_text="Please enter at least two, but no more than 50 characters.",
    )

    gender = fields.ChoiceField(
        label="Gender",
        choices=[('m', "Male"), ('f', "Female")],
        widget=widgets.RadioSelect,
        error_messages={'invalid_choice': "Please select your gender."},
    )

    pregnat = fields.BooleanField(
        label="Are you pregnat?",
        required=False,
        widget=widgets.CheckboxInput(attrs={'disable-if': ".gender!='f'"})
    )

    def clean(self):
        cd = super().clean()
        if cd['first_name'].lower().startswith("john") and cd['last_name'].lower().startswith("doe"):
            raise ValidationError(f"{cd['first_name']} {cd['last_name']} is persona non grata here!")
        return cd


sample_person_data = {
    'first_name': "John",
    'last_name': "Doe",
    'gender': 'm',
    'accept': True,
}
