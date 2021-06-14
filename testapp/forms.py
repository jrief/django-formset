from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.exceptions import ValidationError
from django.forms import forms, fields, widgets, models

from formset.mixins import default, bootstrap, bulma, foundation, tailwind
from formset.widgets import Selectize, UploadedFileInput

from testapp.models import PayloadModel, ChoicesModel


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
    )

    first_name = fields.RegexField(
        r'^[A-Z][a-z -]*$',
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

    avatar = fields.FileField(
        label="Avatar",
        widget=UploadedFileInput,
        required=True,
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
    )

    continent = fields.ChoiceField(
        label="Living on continent",
        choices=CONTINENT_CHOICES,
        required=True,
        initial='',
        error_messages={'invalid_choice': "Please select your continent."},
    )

    # choice = models.ModelChoiceField(
    #     queryset=ChoicesModel.objects.filter(tenant=1),
    #     label="Choose from",
    #     empty_label="Select an option",
    #     widget=Selectize(search_lookup='label__icontains'),
    # )

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

    class Meta:
        model = PayloadModel
        exclude = ['payload']
        entangled_fields = {'payload': ['last_name', 'first_name', 'sex', 'email', 'subscribe',
            'phone', 'birth_date', 'continent', 'weight', 'height', 'used_transportation',
            'preferred_transportation', 'available_transportation', 'notifyme', 'annotation',
            'agree', 'password', 'confirmation_key']}

    def __str__(self):
        return self.as_field_groups()


class DefaultMixinForm(default.FormMixin, SubscribeForm):
    pass


class BootstrapMixinForm(bootstrap.FormMixin, SubscribeForm):
    pass


class BulmaMixinForm(bulma.FormMixin, SubscribeForm):
    pass


class FoundationMixinForm(foundation.FormMixin, SubscribeForm):
    pass


class TailwindMixinForm(tailwind.FormMixin, SubscribeForm):
    pass


class UploadForm(forms.Form):
    name = 'upload'

    file = fields.FileField(
        label="Choose file",
        widget=UploadedFileInput,
        required=True,
    )


class PersonForm(forms.Form):
    name = 'persona'

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

    accept = fields.BooleanField(
        label="Accept terms and conditions",
        initial=False,
    )

    def clean(self):
        cd = super().clean()
        if cd['first_name'].lower().startswith("john") and cd['last_name'].lower().startswith("doe"):
            raise ValidationError(f"{cd['first_name']} {cd['last_name']} is persona non grata here!")
        return cd


class SelectForm(forms.Form):
    name = 'select'

    choice = models.ModelChoiceField(
        queryset=ChoicesModel.objects.filter(tenant=1),
        label="Choose from",
        empty_label="Select an option",
        widget=Selectize(search_lookup='label__icontains'),
    )
