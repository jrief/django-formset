.. _default-widgets:

===============
Default Widgets
===============

**django-formset** supports all standard widgets, Django provides out of the box. This includes the
``MultipleChoiceField`` with the ``CheckboxSelectMultiple`` widget and the ``ChoiceField`` with the
``RadioSelect`` widget. The latter also includes option groups and is explicitly mentioned here,
because these special cases are rarely used and none of the supported CSS frameworks even mention
them.

This example form uses all standard widgets Django provides out of the box. They do not require
any client-side implementation and are implemented in pure HTML, just using specially designed
widget templates.

.. django-view:: complete_view
	:view-function: CompleteView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'complate-result'})

	from django.contrib.auth.hashers import PBKDF2PasswordHasher
	from django.core.exceptions import ValidationError
	from django.forms import fields, forms, widgets
	from django.utils.timezone import now
	
	from formset.views import FormView
	
	def validate_password(value):
	    pwhasher = PBKDF2PasswordHasher()
	    if not pwhasher.verify(value, 'pbkdf2_sha256$216000$salt$NBY9WN4TPwv2NZJE57BRxccYp0FpyOu82J7RmaYNgQM='):
	        raise ValidationError("The password is wrong.")
	
	class CompleteForm(forms.Form):
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
	        help_text="Allowed date format: yyyy-mm-dd",
	        initial=now,
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
	        error_messages={'min_value': "You are too lightweight.", 'max_value': "You are too heavy."},
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

	class CompleteView(FormView):
	    form_class = CompleteForm
	    template_name = "form.html"
	    success_url = "/success"

Not all of these widgets might be suitable for your web application. Checkboxes or radio selects
with more than a handful of elements are difficult to handle. Using the HTML element
``<select … multiple>`` often also is not an option, because many users do not know how to select
multiple options using the shift- or command-key.

The savvy reader might have noticed that some checkbox and radio-select groups are aligned
horizontally, while others are aligned vertically. This is intended behavior and can be configured
using the parameter ``max_options_per_line`` when configuring its :ref:`form-renderer`.

In addition to the default widgets shown here, **django-formset** offers a set of
:ref:`alternative-widgets`, which offer more functionality but also require a client-side
implementation.
