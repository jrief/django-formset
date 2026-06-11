from datetime import timezone, timedelta

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
    enable = fields.BooleanField(
        label="Enable Birthdate",
        initial=False,
        required=False,
    )
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(2021, 7, 9, tzinfo=timezone.utc),
        widget=DateTextbox(attrs={
            'date-format': 'iso',
            'max': lambda: datetime.now(tz=timezone.utc).date() + timedelta(days=1),
            'df-disable': '!.enable',
        }),
    )


class BirthdateCalendarForm(forms.Form):
    enable = fields.BooleanField(
        label="Enable Birthdate",
        initial=False,
        required=False,
    )
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(2021, 7, 9, tzinfo=timezone.utc),
        widget=DateCalendar(attrs={
            'max': lambda: datetime.now(tz=timezone.utc).date() + timedelta(days=1),
            'df-disable': '!.enable',
        }),
    )


class BirthdatePickerForm(forms.Form):
    name = fields.CharField(
        label="Name",
        initial="John Doe",
        disabled=True,
    )
    enable = fields.BooleanField(
        label="Enable Birthdate",
        initial=False,
        required=False,
    )
    birthdate = fields.DateField(
        label="Birthdate",
        initial=datetime(2021, 7, 9, tzinfo=timezone.utc),
        widget=DatePicker(attrs={
            # 'date-format': 'iso',
            'max': lambda: datetime.now(tz=timezone.utc).date() + timedelta(days=1),
            'df-disable': '!.enable',
        }),
    )
