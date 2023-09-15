from datetime import timedelta, timezone

from django.forms import fields, forms
from django.utils.timezone import datetime

from formset.widgets import DateTimeCalendar, DateTimeInput, DateTimePicker, DateTimeTextbox


class MomentInputForm(forms.Form):
    moment = fields.DateTimeField(
        label="Moment",
        widget=DateTimeInput(attrs={
            # 'min': lambda: (now() - timedelta(days=3)).isoformat()[:16],
            # 'max': lambda: (now() + timedelta(days=3)).isoformat()[:16],
        }),
        required=True,
        initial=datetime(2023, 2, 28, 9, 40, tzinfo=timezone.utc),
    )


class MomentBoxForm(forms.Form):
    moment = fields.DateTimeField(
        label="Moment",
        widget=DateTimeTextbox(attrs={
            # 'min': lambda: (now() - timedelta(days=3)).isoformat()[:16],
            # 'max': lambda: (now() + timedelta(days=3)).isoformat()[:16],
            'step': timedelta(minutes=10),
            #'date-format': 'iso',
            #'local-time': '',
        }),
        required=True,
        initial=datetime(2023, 2, 28, 9, 40, tzinfo=timezone.utc),
    )


class MomentCalendarForm(forms.Form):
    moment = fields.DateTimeField(
        label="Moment",
        widget=DateTimeCalendar(attrs={
            'step': timedelta(minutes=10),
        }),
        required=True,
        initial=datetime(2023, 2, 28, 9, 40, tzinfo=timezone.utc),
    )


class MomentPickerForm(forms.Form):
    moment = fields.DateTimeField(
        label="Moment",
        widget=DateTimePicker(attrs={
            # 'min': lambda: (now() - timedelta(days=3)).isoformat()[:16],
            # 'max': lambda: (now() + timedelta(days=3)).isoformat()[:16],
            'step': timedelta(minutes=10),
            #'date-format': 'iso',
            #'local-time': '',
        }),
        required=True,
        initial=datetime(2023, 2, 28, 9, 40, tzinfo=timezone.utc),
    )
