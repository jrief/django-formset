.. _date-time-range:

=========================
Date- and Date-Time Range
=========================

While modern browsers offer input fields with built-in date and date-time pickers, they do not offer
anything like that to select an interval from one date to another one. For this purpose,
**django-formset** offers a variant of the :ref:`date-time-input` fields with an interface allowing
to select a range of dates or date-times.


Date Range Field
================

**django-formset** offers the extra field :class:`formset.formfields.DateRangeField`. This is a
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
	from formset.formfields import DateRangeField
	from formset.widgets import DateRangePicker

	class BookingForm(forms.Form):
	    date_range = DateRangeField(
	        widget=DateRangePicker(),
	    )

The ``DateRangeField`` can be configured to use one of these widgets:

* :class:`formset.widgets.DateRangePicker` – as shown here: The picker has a calendar dialog popping
  up when the user clicks on the calendar icon. The lower- and upper dates must be entered into the
  same calendar sheet.
* :class:`formset.widgets.DateRangeDualPicker` – the picker has two separate calendar sheets for
  entering the lower- and upper date.
* :class:`formset.widgets.DateRangeTextbox` – just an input field accepting two dates.
* :class:`formset.widgets.DateRangeCalendar` – just the calendar widget without an input field.
* :class:`formset.widgets.DateRangeDualCalendar` – widget without an input field, but with two
  separate calendar sheets, one for entering the lower- and one to enter the upper date.

If this field shall be initialized with a default value using attribute ``initial``, the given value
must be a two-tuple or list of two dates. Then the first date is the lower date and the second date
is the upper date of the given date range.

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

.. note:: The view uses the :class:`formset.calendar.CalendarResponseMixin` to render the calendar,
	which is rendered by the server. This mixin is not required if you use the
	:class:`formset.widgets.DateRangeTextbox` widget.


Date-Time Range Field
=====================

**django-formset** offers the extra fields :class:`formset.formfields.DateTimeRangeField`. This is a
subclasses of Django's :class:`django.forms.fields.MultiValueField` and maps two fields of type
:class:`django.forms.fields.DateTimeField` to a single field.

Usually it is sufficient to let the user select a range in a given interval, say a quartely or a
full hour, without choosing individual minutes. This is the default behaviour of the datetime
calendar widgets: when no ``step`` attribute is provided, or when ``step`` is set to
``timedelta(hours=1)`` or larger, the calendar only shows hour cells with no minute sub-rows.

.. django-view:: shift_form
	:caption: form.py

	from datetime import timedelta
	from django import forms
	from django.utils.timezone import datetime
	from formset.formfields import DateTimeRangeField
	from formset.widgets import DateTimeRangePicker

	class ShiftForm(forms.Form):
	    shift = DateTimeRangeField(
	        label="Shift",
	        widget=DateTimeRangePicker(),
	        initial=(
	            datetime(2026, 4, 7, 8, 0),
	            datetime(2026, 4, 24, 16, 0),
	        ),
	    )

.. django-view:: shift_view
	:view-function: ShiftView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'shift-calendar-result'}, form_kwargs={'auto_id': 'sh_id_%s'})
	:hide-code:

	from formset.calendar import CalendarResponseMixin
	from formset.views import FormView

	class ShiftView(CalendarResponseMixin, FormView):
	    form_class = ShiftForm
	    template_name = "form.html"
	    success_url = "/success"

The ``DateTimeRangeField`` can be configured to use one of these widgets:

* :class:`formset.widgets.DateTimePicker` – as shown here: The picker has a calendar dialog popping
  up when the user clicks on the calendar icon. The lower- and upper date-timestamps must be entered
  into the same calendar sheet.
* :class:`formset.widgets.DateTimeRangeDualPicker` – the picker has two separate calendar sheets for
  entering the lower- and upper date and timestamps.
* :class:`formset.widgets.DateTimeRangeTextbox` – as input field accepting two timestamps.
* :class:`formset.widgets.DateTimeRangeCalendar` – just the calendar widget without an input field.
* :class:`formset.widgets.DateTimeRangeDualCalendar` – widget without an input field, but with two
  separate calendar sheets, one for entering the lower- and one to enter the upper date.

Here the calendar only renders the hour cells. If the granularity of the calendar is shorter, a
minutes view is rendered as well. Having to deal with two timestamps inside the same calendar sheet
can be tricky.

When using the calendar picker in hour mode, there is one more thing to consider: After the starting
date has been selected, the calendar picker will show an additional cell named "24h" or "12am". This
special cell is added, so that the user can select end of day and doesn't have to navigate to the
next day and chose midnight there.


Date-Time-Range Picker with Dual Calendar Sheets
------------------------------------------------

.. versionadded:: 2.3

**django-formset** also offers the widget :class:`formset.widgets.DateTimeRangeDualPicker`. This
widget shows two separate calendar sheets for entering the lower and upper date- and timestamps.
This makes it much easier to enter a date-time range, especially when the calendar is rendered in
minutes mode.

.. django-view:: schedule_form
	:caption: form.py

	from datetime import timedelta
	from django import forms
	from django.utils.timezone import datetime
	from formset.formfields import DateTimeRangeField
	from formset.widgets import DateTimeRangeDualPicker

	class ScheduleForm(forms.Form):
	    date_range = DateTimeRangeField(
	        widget=DateTimeRangeDualPicker(attrs={
	            'step': timedelta(minutes=15),
	        }),
	        initial=(
	            datetime(2026, 9, 9, 9, 45),
	            datetime(2026, 10, 10, 10, 15),
	        ),
	    )


.. django-view:: schedule_view
	:view-function: ScheduleView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'schedule-calendar-result'}, form_kwargs={'auto_id': 'sc_id_%s'})
	:hide-code:

	from formset.calendar import CalendarResponseMixin
	from formset.views import FormView

	class ScheduleView(CalendarResponseMixin, FormView):
	    form_class = ScheduleForm
	    template_name = "form.html"
	    success_url = "/success"

Here we use the :class:`formset.widgets.DateTimeRangeDualPicker` widget, which shows two separate
calendar sheets for entering the lower and upper date. Having to enter two timestamps using one
calendar sheet, can be tricky. Therefore it is recommended to use this widget to facilitate the
input of timestamps.

When using the calendar picker in hour mode, there is one more thing to consider: The calendar sheet
to select the upper date-time will show an additional cell named "24h" or "12am". This special cell
is added, so that the user can select end of day and doesn't have to navigate to the next day and
chose midnight there.

.. note:: The view uses the :class:`formset.calendar.CalendarResponseMixin` to render the calendar,
	which is rendered by the server. This mixin is not required if you use the
	:class:`formset.widgets.DateTimeRangeTextbox` widget.


Date-Time-Range Text Box
------------------------

Configuring a ``DateTimeRangeField`` without a calendar picker makes sense whenever we do not want
to specify a range interval. In this case, we can use the ``DateTimeRangeTextbox`` widget to specify
two timestamps without any granularity.

.. django-view:: appointment_form
	:caption: form.py

	from django import forms
	from django.utils.timezone import datetime
	from formset.formfields import DateTimeRangeField
	from formset.widgets import DateTimeRangeTextbox

	class AppointmentForm(forms.Form):
	    appointment = DateTimeRangeField(
	        label="Appointment",
	        widget=DateTimeRangeTextbox(),
	        initial=(
	            datetime(2026, 4, 8, 14, 33),
	            datetime(2026, 4, 11, 15, 41),
	        ),
	    )

.. django-view:: appointment_view
	:view-function: AppointmentView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'appointment-result'}, form_kwargs={'auto_id': 'ap_id_%s'})
	:hide-code:

	from formset.views import FormView

	class AppointmentView(FormView):
	    form_class = AppointmentForm
	    template_name = "form.html"
	    success_url = "/success"

Since this widget is a plain text input without a calendar sheet, the user can type any valid
date-time down to the minute. No :class:`formset.calendar.CalendarResponseMixin` is needed on the
view.


Extra Widget Attributes
=======================

The date- and date-time-range widgets accept the following extra attributes:

* ``step``: This attribute specifies the granularity of the calendar for the widgets
  ``DateTimeRangePicker``, ``DateTimeRangeDualPicker``, ``DateTimeRangeCalendar`` and
  ``DateTimeRangeDualCalendar``. The value of this attribute must be a ``datetime.timedelta``
  object.
* ``min``: This attribute specifies the minimum date or date-time that can be selected in the
  calendar. The value of this attribute must be a date or date-time object. List items with a date
  or date-time smaller than this value are disabled in the calendar.
* ``max``: This attribute specifies the maximum date or date-time that can be selected in the
  calendar. The value of this attribute must be a date or date-time object. List items with a date
  or date-time larger than this value are disabled in the calendar.
* ``date-format``: This attribute specifies the format in which the date or date-time is displayed
  in the input field for the widgets ``DateRangeTextbox``, ``DateTimeRangeTextbox``,
  ``DateRangePicker``, ``DateRangeDualPicker``, ``DateTimeRangePicker`` and
  ``DateTimeRangeDualPicker``. The value of this attribute must be a string in the format or ``iso``
  to use the ISO format. The default is to use the browser's locale setting.
* ``show-upper``: If set to ``True``, the calendar shows the upper date or date-time in the calendar
  sheet. This is only relevant for the widgets ``DateRangePicker``, ``DateTimeRangePicker``,
  ``DateRangeCalendar`` and ``DateTimeRangeCalendar``. The default value is ``False`` which means
  that only the lower date or date-time of any given range is shown in the calendar sheet.


Applying Context to the Calendar
================================

One of the advantages of using a server side rendered calendar sheet is, that we are able to enrich
the rendering context with additional data. This for instance is useful to highlight certain dates.

In this example we emulate a reservation calendar, where only every fifth day is available for
booking. We do this by adding a special CSS class to the calendar cells of the available days and
set the attribute ``disabled`` otherwise.

.. django-view:: reservation_form
	:caption: form.py

	from datetime import datetime
	from formset.calendar import CalendarRenderer, ViewMode
	from formset.formfields import DateRangeField
	from formset.widgets import DateRangeCalendar

	class ReservationRenderer(CalendarRenderer):
	    start_date = datetime.today().date()
	
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


Since this view requires a modified renderer to add the extra context, we must tell our special
mixin class :class:`formset.calendar.CalendarResponseMixin` to use this by passing it as
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
