from datetime import timezone

from django.forms import fields, forms
from django.utils.timezone import datetime

from formset.widgets import DateCalendar, DateInput, DatePicker, DateTextbox


class BirthdateInputForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(2021, 7, 9, tzinfo=timezone.utc),
        widget=DateInput(attrs={
            'max': lambda: datetime.now(tz=timezone.utc).date(),
        }),
    )


class BirthdateBoxForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(2021, 7, 9, tzinfo=timezone.utc),
        widget=DateTextbox(attrs={
            # 'date-format': 'iso',
            # 'min': datetime(2023, 2, 28).isoformat()[:16],
            'max': lambda: datetime.now(tz=timezone.utc).date(),
        }),
    )


class BirthdateCalendarForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(2021, 7, 9, tzinfo=timezone.utc),
        widget=DateCalendar(attrs={
            'max': lambda: datetime.now(tz=timezone.utc).date(),
        }),
    )


class BirthdatePickerForm(forms.Form):
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(2021, 7, 9, tzinfo=timezone.utc),
        widget=DatePicker(attrs={
            # 'date-format': 'iso',
            # 'min': datetime(2023, 2, 28).isoformat()[:16],
            'max': lambda: datetime.now(tz=timezone.utc).date(),
        }),
    )

