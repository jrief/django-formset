.. _date-time-range:

=========================
Date- and Date-Time Range
=========================

While modern browsers offer input fields with built-in date and date-time pickers, they do not offer
anything like that to select an interval from one date to another one. Therefore, **django-formset**
offers a variant of the :ref:`date-time-input` fields with an interface allowing to select a range
of dates or date-times.


Date Range Field
================

**django-formset** offers the extra field :class:`formset.fields.DateRangeField`. This is a
subclasses of Django's :class:`django.forms.fields.MultiValueField` and maps two fields of type
:class:`django.forms.fields.DateField` field. The field's value is a tuple of two dates, the start
and the end date of the given range.

This field shall be used in combination with one of the provided widgets:

Date Range Picker
-----------------

In a Django form class, the field can be used like this:

.. django-view:: booking_form
	:caption: form.py

	from django import forms
	from formset.ranges import DateRangeField, DateRangePicker

	class BookingForm(forms.Form):
	    date_range = DateRangeField(
	        widget=DateRangePicker(),
	    )

The `DateRangeField` can be configured to use one of these widgets:

* :class:`formset.widgets.DateRangePicker` – shown here
* :class:`formset.widgets.DateRangeTextox` – just an input field accepting two dates 
* :class:`formset.widgets.DateRangeCalendar` – just the calendar widget without input field

If this field shall be initialized with a default value using attribute ``initial``, the given value
must be a tuple or list of two dates. Then the first date is the start date, the second date is the
end date of the range.

The view handling this form can be implemented like this:

.. django-view:: booking_view
	:view-function: BookingView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'booking-picker-result'}, form_kwargs={'auto_id': 'bp_id_%s'})
	:caption: views.py

	from formset.calendar import CalendarResponseMixin
	from formset.views import FormView

	class BookingView(CalendarResponseMixin, FormView):
	    form_class = BookingForm
	    template_name = "form.html"
	    success_url = "/success"

Note that the view uses the :class:`formset.calendar.CalendarResponseMixin` to render the calendar,
which is rendered by the server. This mixin is not required if you use the
:class:`formset.widgets.DateRangeTextbox` widget.


Date-Time Range Field
=====================

**django-formset** offers the extra fields :class:`formset.fields.DateTimeRangeField`. This is a
subclasses of Django's :class:`django.forms.fields.MultiValueField` and maps two fields of type
:class:`django.forms.fields.DateTimeField` to a single field.

.. django-view:: schedule_form
	:caption: form.py

	from datetime import timedelta
	from django import forms
	from django.utils.timezone import datetime
	from formset.ranges import DateTimeRangeField, DateTimeRangePicker

	class ScheduleForm(forms.Form):
	    date_range = DateTimeRangeField(
	        widget=DateTimeRangePicker(attrs={
	            'step': timedelta(minutes=15),
	        }),
	        initial=(
	            datetime(2023, 9, 9, 9, 45),
	            datetime(2023, 10, 10, 10, 15),
	        ),
	    )

The `DateTimeRangeField` can be configured to use one of these widgets:

* :class:`formset.widgets.DateTimeRangePicker` – shown here
* :class:`formset.widgets.DateTimeRangeTextbox` – as input field accepting two timestamps  
* :class:`formset.widgets.DateTimeRangeCalendar` – just the calendar widget without input field

Configuring a `DateTimeRangeField` without a calendar picker makes sense whenever we do not want to
specify a range interval. In this case, we can use the `DateTimeRangeTextbox` widget to specify two
timestamps without any granularity.

.. django-view:: schedule_view
	:view-function: ScheduleView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'schedule-calendar-result'}, form_kwargs={'auto_id': 'sc_id_%s'})
	:hide-code:

	from formset.calendar import CalendarResponseMixin
	from formset.views import FormView

	class ScheduleView(CalendarResponseMixin, FormView):
	    form_class = ScheduleForm
	    template_name = "form.html"
	    success_url = "/success"

When using the calendar picker in hour mode, there is one more thing to consider: After the starting
date has been selected, the calendar picker will show the an additional cell named "24h" or "12am".
This is so that the user can select end of day and doesn't have to navigate to the next day and
chose midnight there.


Applying Context to the Calendar
================================

One of the advantages of using a server side rendered calendar sheet is, that we are able to enrich
the rendering context with additional data. This for instance is useful to highlight certain dates.

Here for instance we emulate a reservation calendar, where only every fifth day is available for
booking. We do this by adding a special CSS class to the calendar cells of the available days and
set the attribute ``disabled`` otherwise.

.. django-view:: reservation_form
	:caption: form.py

	from datetime import datetime
	from formset.calendar import CalendarRenderer, ViewMode
	from formset.ranges import DateRangeField, DateRangeCalendar

	class ReservationRenderer(CalendarRenderer):
	    start_date = start_date = datetime.today().date()
	
	    def get_template_name(self, view_mode):
	        if view_mode == ViewMode.weeks:
	            return 'calendar/weeks-reservation.html'
	        return super().get_template_name(view_mode)
	
	    def get_context_weeks(self):
	        context = super().get_context_weeks()
	        monthdays = []
	        for date_string, monthday, css_class in context['monthdays']:
	            delta = self.start_date - datetime.fromisoformat(date_string).date()
	            available = delta.days % 5 == 0
	            if available:
	                css_class += ' available'
	            monthdays.append((date_string, monthday, css_class, available))
	        context['monthdays'] = monthdays
	        return context

	class ReservationForm(forms.Form):
	    date_range = DateRangeField(
	        label="Date Range",
	        widget=DateRangeCalendar(calendar_renderer=ReservationRenderer),
	    )


Since this view requires a modified renderer to add additional context, we must tell our special
mixin class :class:`formset.calendar.CalendarResponseMixin` to use that by passing it as
``calendar_renderer_class``:

.. django-view:: reservation_view
	:view-function: ReservationView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'reservation-result'}, form_kwargs={'auto_id': 'rr_id_%s'})
	:caption: view.py

	class ReservationView(CalendarResponseMixin, FormView):
	    form_class = ReservationForm
	    calendar_renderer_class = ReservationRenderer
	    template_name = "form.html"
	    success_url = "/success"

Here available dates are highlighted in green and disabled dates are grayed out. Note that the
calendar renderer is not limited to highlight dates. It can be used to add any kind of context and
the rendering template can be overwritten to make use of that context.
