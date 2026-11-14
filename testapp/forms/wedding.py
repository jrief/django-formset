from django.forms.fields import CharField, BooleanField, ChoiceField
from django.forms.widgets import CheckboxInput, RadioSelect

from formset.fieldset import Fieldset
from formset.forms import Form


class FianceFieldset(Fieldset):
    first_name = CharField(label="First Name")
    pregnant = BooleanField(
        label="Is pregnant?",
        required=False,
        widget=CheckboxInput(attrs={'df-show': ".gender==='f'"}),
    )
    parental_joy = ChoiceField(
        label="Parental joy?",
        required=False,
        choices=[
            ('low', "Low"),
            ('medium', "Medium"),
            ('high', "High"),
        ],
        widget=RadioSelect(
            attrs={
                'df-show': "..bride.gender==='f'",
                'df-disable': "!..bride.pregnant",
            },
        ),
    )
    gender = ChoiceField(
        label="Gender",
        choices=[
            ('m', "Male"),
            ('f', "Female"),
        ],
        widget=RadioSelect(),
    )


class WeddingForm(Form):
    groom = FianceFieldset(
        legend="Groom",
        initial={'gender': 'm'},
        show_condition="!.single",
    )
    bride = FianceFieldset(
        legend="Bride",
        initial={'first_name': "Olivia", 'gender': 'f'},
    )
    last_name = CharField(
        label="Common Last Name",
        initial="Smith",
    )
    single = BooleanField(
        label="Are you single?",
        required=False,
    )
