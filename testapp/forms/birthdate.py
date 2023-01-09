from django.forms import fields, forms
from django.utils.timezone import datetime

from formset.widgets import DatePicker, DateInput


class BirthdateForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        widget=DatePicker,
        initial=datetime(2023, 3, 3),
    )
