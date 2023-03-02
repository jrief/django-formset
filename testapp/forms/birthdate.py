from datetime import timedelta

from django.forms import fields, forms
from django.utils.timezone import datetime, now, utc

from formset.widgets import DatePicker, DateTimePicker


class BirthdateForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(1981, 7, 9, tzinfo=utc),
        widget=DatePicker(attrs={
            # 'date-format': 'iso',
            'min': datetime(2023, 2, 28).isoformat()[:16],
            'max': datetime(2023, 3, 15).isoformat()[:16],
        }),
    )

    schedule = fields.DateTimeField(
        label="Schedule",
        widget=DateTimePicker(attrs={
            #'min': lambda: (now() - timedelta(days=3)).isoformat()[:16],
            #'max': lambda: (now() + timedelta(days=3)).isoformat()[:16],
            'step': timedelta(minutes=10),
            'date-format': 'iso',
            #'local-time': '',
        }),
        required=False,
        initial=datetime(2023, 2, 28, 9, 40, tzinfo=utc),
    )

    def clean_birthdate(self):
        value = self.cleaned_data['birthdate']
        print(f"Birthday: {value}")
        return value

    def clean_schedule(self):
        value = self.cleaned_data['schedule']
        print(f"Schedule: {value}")
        return value
