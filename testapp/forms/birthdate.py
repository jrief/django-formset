from datetime import timedelta

from django.forms import fields, forms
from django.utils.timezone import datetime, now

from formset.widgets import DatePicker, DateInput


class BirthdateForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        widget=DatePicker(attrs={
            'min': lambda: (now().date() + timedelta(weeks=1)).isoformat(),
            'max': lambda: (now().date() + timedelta(weeks=6)).isoformat(),
        }),
        initial=datetime(2023, 3, 3),
    )
