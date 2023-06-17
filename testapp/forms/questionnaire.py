from django.forms import fields, forms, widgets


class QuestionnaireForm(forms.Form):
    """
    This Form shows how to use the tag attribute ``df-show="…"``.
    """

    full_name = fields.RegexField(
        r'^[A-Z][a-z\-]+\s[ A-Za-z\-]{2,}$',
        label="First and last name",
        min_length=3,
        max_length=100,
        error_messages={'invalid': "A name consist of a first and last name."},
        help_text="Please enter a first- and a last name, starting in upper case.",
    )

    gender = fields.ChoiceField(
        label="Gender",
        choices=[('m', "Male"), ('f', "Female"), ('x', "Inapplicable")],
        widget=widgets.RadioSelect,
        error_messages={'invalid_choice': "Please select your gender."},
    )

    pregnant = fields.BooleanField(
        label="Are you pregnant?",
        required=False,
        widget=widgets.CheckboxInput(attrs={'df-show': ".gender=='f'"})
    )


sample_questionnaire_data = {
    'first_name': "John Doe",
    'gender': 'm',
    'pregnant': False,
}
