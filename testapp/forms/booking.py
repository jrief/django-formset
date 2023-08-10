from django import forms
# from django.contrib.postgres.forms import DateRangeField

from formset.ranges import DateRangeField


class BookingForm(forms.Form):
    date_range = DateRangeField(
    )
