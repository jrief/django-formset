from django import forms

from formset.ranges import DateRangeCalendar, DateRangeField, DateRangePicker, DateRangeTextbox


class BookingBoxForm(forms.Form):
    date_range = DateRangeField(widget=DateRangeTextbox())


class BookingCalendarForm(forms.Form):
    date_range = DateRangeField(widget=DateRangeCalendar())


class BookingPickerForm(forms.Form):
    date_range = DateRangeField(widget=DateRangePicker())
