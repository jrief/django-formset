from datetime import date, timedelta

from django.forms.widgets import DateTimeBaseInput
from django.utils.timezone import datetime

from formset.calendar import CalendarRenderer


class DateInput(DateTimeBaseInput):
    """
    This is a replacement for Django's date widget ``django.forms.widgets.DateInput`` which renders
    as ``<input type="text" ...>``.
    Since we want to use the browsers built-in validation and optionally its date-picker, we have to
    use this alternative implementation using input type ``date``.
    """
    template_name = 'django/forms/widgets/date.html'

    def __init__(self, attrs=None):
        default_attrs = {'type': 'date', 'pattern': r'\d{4}-\d{2}-\d{2}'}
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return value


class DateTimeInput(DateTimeBaseInput):
    template_name = 'django/forms/widgets/date.html'

    def __init__(self, attrs=None):
        default_attrs = {'type': 'datetime-local', 'pattern': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}'}
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, datetime):
            return value.isoformat()[:16]
        return value


class CalendarRendererMixin:
    """
    This mixin adds a calendar to the widget.
    """
    calendar_renderer = CalendarRenderer

    def __init__(self, attrs=None, calendar_renderer=None):
        super().__init__(attrs)
        if calendar_renderer:
            self.calendar_renderer = calendar_renderer
        else:
            self.calendar_renderer = CalendarRenderer

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if isinstance(self.calendar_renderer, type):
            calendar_renderer = self.calendar_renderer(start_datetime=value)
        else:
            calendar_renderer = self.calendar_renderer
        context['calendar'] = calendar_renderer.get_context()
        return context


class DateTextbox(DateTimeBaseInput):
    template_name = 'formset/default/widgets/datetime.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'type': 'date',
            'is': 'django-datefield',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, (date, datetime)):
            return value.strftime('%Y-%m-%d')
        return value


class DateCalendar(CalendarRendererMixin, DateTimeBaseInput):
    template_name = 'formset/default/widgets/calendar.html'
    interval = timedelta(days=1)

    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'date',
            'is': 'django-datecalendar',
        }
        if attrs:
            default_attrs.update(**attrs)
        if attrs and 'step' in attrs:
            self.interval = attrs['step']
            assert self.interval in CalendarRenderer.valid_intervals, \
                f"{self.interval} is not a valid interval for {self.__class__}"
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)

    def format_value(self, value):
        if isinstance(value, (date, datetime)):
            return value.strftime('%Y-%m-%d')
        return value


class DatePicker(CalendarRendererMixin, DateTextbox):
    interval = timedelta(days=1)

    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'is': 'django-datepicker',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if isinstance(self.calendar_renderer, type):
            calendar_renderer = self.calendar_renderer(start_datetime=value)
        else:
            calendar_renderer = self.calendar_renderer
        context['calendar'] = calendar_renderer.get_context(self.interval)
        return context


class DateTimeTextbox(DateTimeBaseInput):
    template_name = 'formset/default/widgets/datetime.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'type': 'datetime-local',
            'is': 'django-datetimefield',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M')
        return value


class DateTimeCalendar(CalendarRendererMixin, DateTimeBaseInput):
    template_name = 'formset/default/widgets/calendar.html'
    interval = timedelta(hours=1)

    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'datetime-local',
            'is': 'django-datetimecalendar',
        }
        if attrs:
            default_attrs.update(**attrs)
        if attrs and 'step' in attrs:
            self.interval = attrs['step']
            assert self.interval in CalendarRenderer.valid_intervals, \
                f"{self.interval} is not a valid interval for {self.__class__}"
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)

    def format_value(self, value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M')
        return value


class DateTimePicker(CalendarRendererMixin, DateTimeTextbox):
    interval = timedelta(hours=1)

    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'is': 'django-datetimepicker',
        }
        if attrs:
            default_attrs.update(**attrs)
        if attrs and 'step' in attrs:
            self.interval = attrs['step']
            assert self.interval in CalendarRenderer.valid_intervals, \
                f"{self.interval} is not a valid interval for {self.__class__}"
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)
