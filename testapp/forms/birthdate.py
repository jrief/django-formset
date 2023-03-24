from datetime import timedelta, timezone

from django.forms import fields, forms
from django.utils.timezone import datetime, now

from formset.widgets import DatePicker, DateTimePicker


class BirthdateForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(2021, 7, 9, tzinfo=timezone.utc),
        widget=DatePicker(attrs={
            # 'date-format': 'iso',
            # 'min': datetime(2023, 2, 28).isoformat()[:16],
            'max': lambda: now().date(),
        }),
    )

    schedule = fields.DateTimeField(
        label="Schedule",
        widget=DateTimePicker(attrs={
            # 'min': lambda: (now() - timedelta(days=3)).isoformat()[:16],
            # 'max': lambda: (now() + timedelta(days=3)).isoformat()[:16],
            'step': timedelta(minutes=10),
            #'date-format': 'iso',
            #'local-time': '',
        }),
        required=False,
        #initial=datetime(2023, 2, 28, 9, 40, tzinfo=utc),
    )

    def clean_birthdate(self):
        value = self.cleaned_data['birthdate']
        print(f"Birthday: {value}")
        return value

    def clean_schedule(self):
        value = self.cleaned_data['schedule']
        print(f"Schedule: {value}")
        return value
