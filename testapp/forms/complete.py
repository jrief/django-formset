from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.exceptions import ValidationError
from django.forms import fields, forms, widgets
from django.utils.timezone import datetime

from formset.widgets import DateInput


def validate_password(value):
    pwhasher = PBKDF2PasswordHasher()
    if not pwhasher.verify(value, 'pbkdf2_sha256$216000$salt$NBY9WN4TPwv2NZJE57BRxccYp0FpyOu82J7RmaYNgQM='):
        raise ValidationError("The password is wrong.")


class CompleteForm(forms.Form):
    """
    This form contains all standard widgets, Django provides out of the box.
    Here is a shortened version of that form.

    .. code-block:: python

        class CompleteForm(forms.Form):
            last_name = fields.CharField(…)
            first_name = fields.RegexField(r'^[A-Z][a-z -]*$', …)
            gender = fields.ChoiceField(choices=…, widget=widgets.RadioSelect, …)
            email = fields.EmailField(…)
            subscribe = fields.BooleanField(…)
            phone = fields.RegexField(r'^\+?[0-9 .-]{4,25}$', …)
            birth_date = fields.DateField(…)
            continent = fields.ChoiceField(…)
            weight = fields.IntegerField(min_value=42, max_value=95, …)
            height = fields.FloatField(min_value=1.45, max_value=1.95, …)
            used_transportation = fields.MultipleChoiceField(widget=widgets.CheckboxSelectMultiple, …)
            preferred_transportation = fields.ChoiceField(widget=widgets.RadioSelect, …)
            available_transportation = fields.MultipleChoiceField(choices=…, …)
            notifyme = fields.MultipleChoiceField(choices=…, widget=widgets.CheckboxSelectMultiple, …)
            annotation = fields.CharField(…, widget=widgets.Textarea(attrs={'cols': '80', 'rows': '3'}))
            agree = fields.BooleanField(…)
            password = fields.CharField(widget=widgets.PasswordInput, …)
            confirmation_key = fields.CharField(widget=widgets.HiddenInput(), …)

    Instances of this form can be rendered using different recepies:

    * by using the templatetag ``render_form …`` (recommended)
    * by adding ``formset.utils.FormMixin`` to the form class
    * by rendering the form fields, field-by-field

    ------

    """

    CONTINENT_CHOICES = [
        ('', "––– please select –––"), ('am', "America"), ('eu', "Europe"), ('as', "Asia"),
        ('af', "Africa"), ('au', "Australia"), ('oc', "Oceania"), ('an', 'Antartica'),
    ]

    TRANSPORTATION_CHOICES = [
        ("Private Transport", [('foot', "Foot"), ('bike', "Bike"), ('mc', "Motorcycle"), ('car', "Car")]),
        ("Public Transport", [('taxi', "Taxi"), ('bus', "Bus"), ('train', "Train"), ('ship', "Ship"), ('air', "Airplane")]),
    ]

    NOTIFY_BY = [
        ('postal', "Letter"), ('email', "EMail"), ('phone', "Phone"), ('sms', "SMS"),
    ]

    last_name = fields.CharField(
        label="Last name",
        min_length=2,
        max_length=50,
        help_text="Please enter at least two characters",
    )

    first_name = fields.RegexField(
        r'^[A-Z][ a-z\-]*$',
        label="First name",
        error_messages={'invalid': "A first name must start in upper case."},
        help_text="Must start in upper case followed by one or more lowercase characters.",
    )

    gender = fields.ChoiceField(
        label="Gender",
        choices=[('m', "Male"), ('f', "Female")],
        widget=widgets.RadioSelect,
        error_messages={'invalid_choice': "Please select your gender."},
    )

    email = fields.EmailField(
        label="E-Mail",
        help_text="Please enter a valid email address",
    )

    subscribe = fields.BooleanField(
        label="Subscribe Newsletter",
        initial=False,
        required=False,
    )

    phone = fields.RegexField(
        r'^\+?[ 0-9.\-]{4,25}$',
        label="Phone number",
        error_messages={'invalid': "Phone number have 4-25 digits and may start with '+'."},
        required=False,
    )

    birth_date = fields.DateField(
        label="Date of birth",
        widget=widgets.DateInput(attrs={'type': 'date', 'pattern': r'\d{4}-\d{2}-\d{2}'}),
        #widget=DateInput,
        help_text="Allowed date format: yyyy-mm-dd",
        initial=datetime(2023, 3, 3),
    )

    continent = fields.ChoiceField(
        label="Living on continent",
        choices=CONTINENT_CHOICES,
        required=True,
        initial='',
        error_messages={'invalid_choice': "Please select your continent."},
    )

    weight = fields.IntegerField(
        label="Weight in kg",
        min_value=42,
        max_value=95,
        error_messages={'min_value': "You are too lightweight.", 'max_value': "You are too obese."},
    )

    height = fields.FloatField(
        label="Height in meters",
        min_value=1.45,
        max_value=1.95,
        widget=widgets.NumberInput(attrs={'step': 0.01}),
        error_messages={'max_value': "You are too tall."},
    )

    used_transportation = fields.MultipleChoiceField(
        label="Used Tranportation",
        choices=TRANSPORTATION_CHOICES,
        widget=widgets.CheckboxSelectMultiple,
        required=True,
        help_text="Used means of tranportation.",
    )

    preferred_transportation = fields.ChoiceField(
        label="Preferred Transportation",
        choices=TRANSPORTATION_CHOICES,
        widget=widgets.RadioSelect,
        help_text="Preferred mean of tranportation.",
    )

    available_transportation = fields.MultipleChoiceField(
        label="Available Tranportation",
        choices=TRANSPORTATION_CHOICES,
        help_text="Available means of tranportation.",
    )

    notifyme = fields.MultipleChoiceField(
        label="Notification",
        choices=NOTIFY_BY,
        widget=widgets.CheckboxSelectMultiple,
        required=True,
        help_text="Must choose at least one type of notification",
    )

    annotation = fields.CharField(
        label="Annotation",
        required=True,
        widget=widgets.Textarea(attrs={'cols': '80', 'rows': '3'}),
    )

    agree = fields.BooleanField(
        label="Agree with our terms and conditions",
        initial=False,
    )

    password = fields.CharField(
        label="Password",
        widget=widgets.PasswordInput,
        validators=[validate_password],
        help_text="The password is 'secret'",
    )

    confirmation_key = fields.CharField(
        max_length=40,
        required=True,
        widget=widgets.HiddenInput(),
        initial='hidden value',
    )


sample_complete_data = {
    'first_name': "John",
    'last_name': "Doe",
    'gender': 'm',
    'email': 'john.doe@example.org',
    'subscribe': True,
    'phone': '+1 234 567 8900',
    'birth_date': datetime(2000, 5, 18),
    'continent': 'eu',
    'available_transportation': ['foot', 'taxi'],
    'preferred_transportation': 'car',
    'used_transportation': ['foot', 'bike', 'car', 'train'],
    'height': 1.82,
    'weight': 81,
    'traveling': ['bike', 'train'],
    'notifyme': ['email', 'sms'],
    'annotation': "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    'password': 'secret',
}
