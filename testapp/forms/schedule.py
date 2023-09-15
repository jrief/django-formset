from datetime import timedelta

from django import forms
from django.utils.timezone import datetime

from formset.ranges import DateTimeRangeCalendar, DateTimeRangeField, DateTimeRangePicker, DateTimeRangeTextbox


class ScheduleBoxForm(forms.Form):
    date_range = DateTimeRangeField(widget=DateTimeRangeTextbox())


class ScheduleCalendarForm(forms.Form):
    date_range = DateTimeRangeField(
        widget=DateTimeRangeCalendar(attrs={
            'step': timedelta(minutes=10),
        }),
        initial=(
            datetime(2023, 10, 10, 9, 40),
            datetime(2023, 10, 10, 16, 10),
        ),
    )


class SchedulePickerForm(forms.Form):
    date_range = DateTimeRangeField(
        widget=DateTimeRangePicker(attrs={
            'step': timedelta(minutes=10),
        }),
        initial=(
            datetime(2023, 10, 10, 9, 40),
            datetime(2023, 10, 10, 16, 10),
        ),
    )
