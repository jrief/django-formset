from datetime import date

from django import forms

from formset.ranges import DateRangeCalendar, DateRangeField, DateRangePicker, DateRangeTextbox


class BookingBoxForm(forms.Form):
    date_range = DateRangeField(widget=DateRangeTextbox())


class BookingCalendarForm(forms.Form):
    date_range = DateRangeField(
        widget=DateRangeCalendar(),
        initial=[
            date(2023, 5, 18),
            date(2023, 10, 12),
        ],
    )


class BookingPickerForm(forms.Form):
    date_range = DateRangeField(
        widget=DateRangePicker(),
        initial=[
            date(2023, 5, 18),
            date(2023, 10, 12),
        ],
    )
