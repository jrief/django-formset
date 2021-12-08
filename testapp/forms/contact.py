from django.core.exceptions import ValidationError
from django.forms import fields, forms

from formset.collection import FormCollection
from formset.renderers.default import FormRenderer as DefaultFormRenderer

from .person import PersonForm


class ProfessionForm(forms.Form):
    company = fields.CharField(
        label="Company",
        min_length=2,
        max_length=50,
        help_text="The company's name",
    )

    job_title = fields.CharField(
        label="Job Title",
        max_length=50,
        required=False,
    )


class SimpleContactCollection(FormCollection):
    person = PersonForm()

    profession = ProfessionForm()


class DefaultContactCollection(FormCollection):
    """
    Used to check, if the renderer can be overridden again.
    """
    person = PersonForm(renderer=DefaultFormRenderer())

    profession = ProfessionForm()


class PhoneNumberForm(forms.Form):
    phone_number = fields.RegexField(
        r'^[01+][0-9 .-]+$',
        label="Phone Number",
        min_length=2,
        max_length=20,
        help_text="Valid phone numbers start with + or 0 followed by digits and spaces",
    )

    label = fields.ChoiceField(
        label="Label",
        choices=[
            ('home', "Home"),
            ('work', "Work"),
            ('mobile', "Mobile"),
            ('other', "Other"),
        ],
    )

    def clean_phone_number(self):
        value = self.cleaned_data['phone_number']
        if value.replace(' ', '') == '+123456789':
            raise ValidationError("Are you kidding me?")
        return value


class PhoneNumberCollection(FormCollection):
    min_siblings = 1
    max_siblings = 5
    extra_siblings = 1

    number = PhoneNumberForm()


class ContactCollection(FormCollection):
    person = PersonForm()

    numbers = PhoneNumberCollection()


class ContactCollectionList(FormCollection):
    min_siblings = 0
    extra_siblings = 1

    person = PersonForm()

    numbers = PhoneNumberCollection(
        min_siblings=1,
        max_siblings=5,
        extra_siblings=1,
    )
