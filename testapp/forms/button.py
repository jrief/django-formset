from time import sleep

from django.core.exceptions import ValidationError
from django.forms import fields, forms


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
