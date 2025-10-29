from datetime import date

from django.forms.utils import to_current_timezone
from django.utils.timezone import datetime, is_naive

from formset.widgets import DateCalendar, DatePicker, DateTextbox, DateTimeCalendar, DateTimePicker, DateTimeTextbox


class DateRangeMixin:
    def format_value(self, values):
        if values is None:
            return ''
        try:
            from django.db.backends.postgresql.psycopg_any import DateRange
            if isinstance(values, DateRange):
                values = values.lower, values.upper
        except ImportError:
            pass
        if isinstance(values, (list, tuple)) and len(values) == 2:
            if any(v is None for v in values):
                return ''
            if all(isinstance(v, date) for v in values):
                return ';'.join(v.strftime('%Y-%m-%dT00:00') for v in values)
        return values


class DateRangeCalendar(DateRangeMixin, DateCalendar):
    template_name = 'formset/default/widgets/calendar.html'

    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T00:00;\d{4}-\d{2}-\d{2}T00:00',
            'is': 'django-daterangecalendar',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateRangePicker(DateRangeMixin, DatePicker):
    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T00:00;\d{4}-\d{2}-\d{2}T00:00',
            'is': 'django-daterangepicker',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateRangeTextbox(DateRangeMixin, DateTextbox):
    def __init__(self, attrs=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T00:00;\d{4}-\d{2}-\d{2}T00:00',
            'is': 'django-daterangefield',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)


class DateTimeRangeMixin:
    def format_value(self, values):
        if values is None:
            return ''
        try:
            from django.db.backends.postgresql.psycopg_any import DateTimeTZRange
            if isinstance(values, DateTimeTZRange):
                values = values.lower, values.upper
        except ImportError:
            pass
        if isinstance(values, (list, tuple)) and len(values) == 2:
            if any(v is None for v in values):
                return ''
            if all(isinstance(v, datetime) for v in values):
                if any(is_naive(v) for v in values):
                    return ';'.join(v.strftime('%Y-%m-%dT%H:%M') for v in values)
                return ';'.join(to_current_timezone(v).strftime('%Y-%m-%dT%H:%M') for v in values)
        return values


class DateTimeRangeCalendar(DateTimeRangeMixin, DateTimeCalendar):
    template_name = 'formset/default/widgets/calendar.html'

    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2};\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
            'is': 'django-datetimerangecalendar',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateTimeRangePicker(DateTimeRangeMixin, DateTimePicker):
    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2};\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
            'is': 'django-datetimerangepicker',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateTimeRangeTextbox(DateTimeRangeMixin, DateTimeTextbox):
    def __init__(self, attrs=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2};\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
            'is': 'django-datetimerangefield',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)
