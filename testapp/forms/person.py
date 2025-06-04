from django.core.exceptions import ValidationError
from django.forms import fields, forms, widgets

from formset.forms import FormMixin, ModelForm
from formset.formfields import DateRangeField
from formset.formfields.richtext import RichTextField
from formset.renderers.bootstrap import FormRenderer as BootstrapFormRenderer
from formset.widgets import DatePicker, DateTimePicker, DualSelector, PhoneNumberInput, Selectize, UploadedFileInput

from testapp.models import PersonModel
from .customer import AddressFieldset


class SimplePersonForm(forms.Form):
    """
    This is a simple form used to show how to withhold various feedback messages nearby the
    offending fields. This is done by adding the attribute ``withhold-feedback="..."`` with one
    or a combination of those values: ``messages``, ``errors``, ``warnings`` and/or ``success``.
    """
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
        max_length=50,
    )


class PersonForm(SimplePersonForm):
    def clean(self):
        cd = super().clean()
        if cd.get('first_name', '').lower().startswith("john") and cd.get('last_name', '').lower().startswith("doe"):
            raise ValidationError(f"{cd['first_name']} {cd['last_name']} is persona non grata here!")
        return cd


class BootstrapRenderedPersonForm(FormMixin, PersonForm):
    """
    This form class shows how to use a custom renderer. The form then can be rendered using ``{{ form }}``
    """
    default_renderer = BootstrapFormRenderer(
        field_css_classes='row mb-3',
        label_css_classes='col-sm-3',
        control_css_classes='col-sm-9',
    )



sample_person_data = {
    'first_name': "John",
    'last_name': "Doe",
}


class ModelPersonForm(ModelForm):
    field_order = ['full_name', 'avatar', 'validity', 'activity_days', 'activity_datetime', 'about', 'phone_number']
    activity_datetime = fields.DateTimeField(
        label="Activity timestamp",
        widget=DateTimePicker,
        required=False,
    )
    address = AddressFieldset()
    activity_days = fields.IntegerField(
        label="Activity days",
    )
    validity = DateRangeField(
        label="Validity",
        required=False,
        help_text="This field is not saved in the database.",
    )
    about = RichTextField(
        label="About",
        required=False,
    )
    phone_number = fields.CharField(
        label="Phone number",
        required=False,
        widget=PhoneNumberInput,
    )

    class Meta:
        model = PersonModel
        fields = '__all__'
        fields_map = {'extra_data': [
            'about', 'activity_datetime', 'activity_days', 'phone_number', 'address.postal_code', 'address.city',
            'validity',
        ]}
        widgets = {
            'avatar': UploadedFileInput,
            'gender': widgets.RadioSelect,
            'birth_date': DatePicker,
            'opinion': Selectize(search_lookup='label__icontains'),
            'opinions': DualSelector(search_lookup='label__icontains'),
        }
