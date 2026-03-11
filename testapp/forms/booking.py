from datetime import date

from django import forms

from formset.formfields import DateRangeField
from formset.widgets import (
    DateRangeCalendar, DateRangeDualCalendar, DateRangePicker, DateRangeDualPicker, DateRangeTextbox
)


class BookingBoxForm(forms.Form):
    date_range = DateRangeField(widget=DateRangeTextbox())


class BookingCalendarForm(forms.Form):
    date_range = DateRangeField(
        widget=DateRangeCalendar(),
        initial=[
            date(2024, 5, 18),
            date(2024, 10, 12),
        ],
    )


class BookingDualCalendarForm(forms.Form):
    date_range = DateRangeField(
        widget=DateRangeDualCalendar(),
    )


class BookingPickerForm(forms.Form):
    date_range = DateRangeField(
        widget=DateRangePicker(),
        initial=[
            date(2023, 5, 18),
            date(2023, 10, 12),
        ],
    )


class BookingDualPickerForm(forms.Form):
    date_range = DateRangeField(
        widget=DateRangeDualPicker(),
    )
