from datetime import timedelta

from django.forms import fields, forms
from django.utils.timezone import datetime, now

from formset.widgets import DatePicker, DateTimePicker


class BirthdateForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        widget=DatePicker(),
#        initial=datetime(1981, 7, 9),
    )

    schedule = fields.DateTimeField(
        label="Schedule",
        widget=DateTimePicker(attrs={
            'min': lambda: (now().date() - timedelta(days=1)).isoformat(),
            'max': lambda: (now().date() + timedelta(weeks=30)).isoformat(),
            'step': timedelta(minutes=60),
        }),
        initial=datetime(2023, 2, 12, 9, 0),
    )
