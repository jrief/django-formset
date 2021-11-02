from django.core.exceptions import ValidationError
from django.forms import fields, forms

from formset.collection import FormCollection
from formset.renderers.bootstrap import FormRenderer as BootstrapFormRenderer
from formset.renderers.default import FormRenderer as DefaultFormRenderer


class PersonForm(forms.Form):
    default_renderer = BootstrapFormRenderer(
        form_css_classes='row',
        field_css_classes={'*': 'mb-2 col-12', 'email': 'mb-2 col-8', 'email_label': 'mb-2 col-4'},
    )

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

    email = fields.EmailField(
        label="E-Mail",
        help_text="Please enter a valid email address",
    )

    email_label = fields.ChoiceField(
        label="Label",
        choices=[
            ('home', "Home"),
            ('vocational', "Vocational"),
            ('other', "Other"),
        ],
        initial='home'
    )


sample_person_data = {
    'first_name': "John",
    'last_name': "Doe",
    'email': "john.doe@example.com",
}


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
    default_renderer = BootstrapFormRenderer(
        form_css_classes='row',
        field_css_classes='mb-2 col-12'
    )

    person = PersonForm()

    profession = ProfessionForm()


class DefaultContactCollection(FormCollection):
    """
    Used to check, if the renderer can be overridden again.
    """
    person = PersonForm(renderer=DefaultFormRenderer())

    profession = ProfessionForm()


class PhoneNumberForm(forms.Form):
    default_renderer = BootstrapFormRenderer(
        form_css_classes='row',
        field_css_classes={'phone_number': 'mb-2 col-8', 'label': 'mb-2 col-4'},
    )

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
    default_renderer = BootstrapFormRenderer

    person = PersonForm()

    numbers = PhoneNumberCollection()


class ContactCollectionList(FormCollection):
    default_renderer = BootstrapFormRenderer
    min_siblings = 0
    extra_siblings = 1

    person = PersonForm()

    numbers = PhoneNumberCollection(
        min_siblings=1,
        max_siblings=5,
        extra_siblings=1,
    )
