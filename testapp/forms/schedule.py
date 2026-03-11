from datetime import timedelta

from django import forms
from django.utils.timezone import datetime

from formset.formfields import DateTimeRangeField
from formset.widgets import (
    DateTimeRangeCalendar, DateTimeRangeDualCalendar, DateTimeRangePicker, DateTimeRangeDualPicker,
    DateTimeRangeTextbox,
)


class ScheduleBoxForm(forms.Form):
    date_range = DateTimeRangeField(widget=DateTimeRangeTextbox())


class ScheduleCalendarForm(forms.Form):
    date_range = DateTimeRangeField(
        widget=DateTimeRangeCalendar(attrs={
            'step': timedelta(minutes=10),
        }),
        initial=(
            datetime(2024, 9, 9, 9, 40),
            datetime(2024, 10, 10, 16, 10),
        ),
    )


class ScheduleDualCalendarForm(forms.Form):
    date_range = DateTimeRangeField(
        widget=DateTimeRangeDualCalendar(attrs={
            'step': timedelta(minutes=10),
        }),
    )


class SchedulePickerForm(forms.Form):
    date_range = DateTimeRangeField(
        widget=DateTimeRangePicker(
            attrs={
                'step': timedelta(minutes=10),
            },
        ),
        initial=(
            datetime(2024, 9, 9, 9, 0),
            datetime(2024, 10, 10, 0, 10),
        ),
    )


class ScheduleDualPickerForm(forms.Form):
    date_range = DateTimeRangeField(
        widget=DateTimeRangeDualPicker(
            attrs={
                'step': timedelta(minutes=10),
            },
        ),
    )
