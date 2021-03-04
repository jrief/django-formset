from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.exceptions import ValidationError
from django.forms import fields, forms, widgets
from django.utils.timezone import datetime


def validate_password(value):
    pwhasher = PBKDF2PasswordHasher()
    if not pwhasher.verify(value, 'pbkdf2_sha256$216000$salt$NBY9WN4TPwv2NZJE57BRxccYp0FpyOu82J7RmaYNgQM='):
        raise ValidationError('The password is wrong.')


class SubscribeForm(forms.Form):
    name = 'subscribe'

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
        initial='JACK',
    )

    first_name = fields.RegexField(
        r'^[A-Z][a-z -]*$',
        label="First name",
        error_messages={'invalid': "A first name must start in upper case."},
    )

    sex = fields.ChoiceField(
        choices=[('m', 'Male'), ('f', 'Female')],
        widget=widgets.RadioSelect,
        error_messages={'invalid_choice': "Please select your sex."},
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
        r'^\+?[0-9 .-]{4,25}$',
        label="Phone number",
        error_messages={'invalid': "Phone number have 4-25 digits and may start with '+'."},
        widget=fields.TextInput(attrs={'hide-if': 'subscribe'})
    )

    birth_date = fields.DateField(
        label="Date of birth",
        widget=widgets.DateInput(attrs={'type': 'date', 'pattern': r'\d{4}-\d{2}-\d{2}'}),
        help_text="Allowed date format: yyyy-mm-dd",
        initial=datetime(year=1966, month=7, day=9),
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


class SubscribeForm2(forms.Form):
    used_transportation = fields.MultipleChoiceField(
        label="Used Tranportation",
        choices=SubscribeForm.TRANSPORTATION_CHOICES,
        widget=widgets.CheckboxSelectMultiple,
        required=True,
        initial=['air', 'foot'],
        help_text="Used means of tranportation.",
    )


class SubscribeForm3(forms.Form):
    preferred_transportation = fields.ChoiceField(
        label="Preferred Transportation",
        choices=SubscribeForm.TRANSPORTATION_CHOICES,
        widget=widgets.RadioSelect,
        help_text="Preferred mean of tranportation.",
    )
