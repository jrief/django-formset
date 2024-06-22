from time import sleep

from django.core.exceptions import ValidationError
from django.forms import fields, forms, models, widgets

from formset.renderers.bootstrap import FormRenderer as BootstrapFormRenderer
from formset.utils import FormMixin
from formset.widgets import DateInput, Selectize, SelectizeMultiple, UploadedFileInput

from testapp.models import PersonModel


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


class PersonFormBootstrapRenderer(FormMixin, PersonForm):
    """
    This form class shows how to use a custom renderer. The form then can be rendered using ``{{ form }}``
    """
    default_renderer = BootstrapFormRenderer(
        field_css_classes='row mb-3',
        label_css_classes='col-sm-3',
        control_css_classes='col-sm-9',
    )



class ButtonActionsForm(forms.Form):
    """
    This is a simple Django Form with just one input field. It is used to show how to use
    "button actions". On each button inside a ``<django-formset>``, we can attach the event handler
    ``<button click="...">`` to a chain of actions. This attribute then contains a list of actions,
    whose most notables are ``submit -> proceed``.

    This example mimicks a form which takes a few seconds for processing. For time-consuming form
    submission, it is good practice to improve the user experience by giving feedback. Here, the
    button tells its caller, that this action may take some time by displaying a spinner.

    On succeeded submission, the button displays an okay tick for 1.5 seconds before proceeding.

    On failed submission, the button displays a bummer symbol to signalize a failure.

    .. code-block:: html

        <button click="clearErrors -> disable -> spinner -> submit -> okay(1500) -> proceed !~ enable -> bummer(9999)">Submit</button>
    """
    full_name = fields.CharField(
        label="Full name",
        min_length=2,
        max_length=100,
        help_text="Please enter at least two characters",
    )

    def clean(self):
        cleaned_data = super().clean()
        sleep(2.5)
        parts = cleaned_data['full_name'].split()
        if len(parts) < 2:
            raise ValidationError("A valid full name consists of at least a first- and a last name.")
        for part in parts:
            if not part[0].isupper() or not part[1:].islower():
                raise ValidationError("Names have invalid capitalization.")
        return cleaned_data


sample_person_data = {
    'first_name': "John",
    'last_name': "Doe",
}


class ModelPersonForm(models.ModelForm):
    """
    This form is created by Django's helper functions that creates a ModelForm class out of a Django model.
    """

    class Meta:
        model = PersonModel
        fields = '__all__'
        widgets = {
            'avatar': UploadedFileInput,
            'gender': widgets.RadioSelect,
            'birth_date': DateInput,
            'opinion': Selectize(search_lookup='label__icontains'),
            'opinions': SelectizeMultiple(search_lookup='label__icontains', max_items=15),
        }
