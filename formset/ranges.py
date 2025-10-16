from datetime import date

from django.forms import fields
from django.utils.timezone import get_current_timezone, is_naive, make_aware, timezone
from django.utils.translation import gettext_lazy as _

from formset.widgets import DateCalendar, DatePicker, DateTextbox, DateTimeCalendar, DateTimePicker, DateTimeTextbox


class DateTimeRangeMixin:
    def format_value(self, values):
        if isinstance(values, (list, tuple)) and len(values) == 2 and all(isinstance(v, date) for v in values):
            if any(is_naive(v) for v in values):
                values = map(lambda v: make_aware(v, timezone.utc), values)
            tz = get_current_timezone()
            return ';'.join(v.astimezone(tz).strftime('%Y-%m-%dT%H:%M') for v in values)
        return ''


class DateRangeCalendar(DateTimeRangeMixin, DateCalendar):
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


class DateRangePicker(DateTimeRangeMixin, DatePicker):
    def __init__(self, attrs=None, calendar_renderer=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T00:00;\d{4}-\d{2}-\d{2}T00:00',
            'is': 'django-daterangepicker',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs, calendar_renderer=calendar_renderer)


class DateRangeTextbox(DateTimeRangeMixin, DateTextbox):
    def __init__(self, attrs=None):
        default_attrs = {
            'type': 'regex',
            'pattern': r'\d{4}-\d{2}-\d{2}T00:00;\d{4}-\d{2}-\d{2}T00:00',
            'is': 'django-daterangefield',
        }
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)


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


class BaseRangeField(fields.MultiValueField):
    default_error_messages = {
        'invalid': _("Enter two valid values."),
        'bound_ordering': _("The start of the range must not exceed the end of the range."),
    }

    def __init__(self, widget, **kwargs):
        kwargs.setdefault('required', True)
        kwargs.setdefault('require_all_fields', kwargs['required'])
        kwargs.setdefault('fields', [
            self.base_field(required=kwargs['required']),
            self.base_field(required=kwargs['required']),
        ])
        self.range_kwargs = {}
        if default_bounds := kwargs.pop('default_bounds', None):
            self.range_kwargs = {'bounds': default_bounds}
        super().__init__(widget=widget, **kwargs)

    def prepare_value(self, values):
        raise NotImplementedError("Subclasses must implement this method.")

    def compress(self, values):
        if not values:
            return None, None
        return values

    def validate(self, values):
        lower, upper = values
        if lower is not None and upper is not None and lower > upper:
            raise fields.ValidationError(
                self.error_messages['bound_ordering'],
                code='bound_ordering',
            )


class DateRangeField(BaseRangeField):
    default_error_messages = {
        'invalid': _("Enter two valid dates."),
        'bound_ordering': _("The start date must be before the end date."),
    }
    base_field = fields.DateField

    def __init__(self, **kwargs):
        kwargs.setdefault('widget', DateRangePicker())
        super().__init__(**kwargs)

    def prepare_value(self, values):
        if isinstance(values, (list, tuple)) and len(values) == 2:
            return ';'.join(map(lambda v: f'{v.isoformat()[:10]}T00:00', values))
        return ''


class DateTimeRangeField(DateRangeField):
    base_field = fields.DateTimeField

    def __init__(self, **kwargs):
        kwargs.setdefault('widget', DateTimeRangePicker())
        super().__init__(**kwargs)

    def prepare_value(self, values):
        if isinstance(values, (list, tuple)) and len(values) == 2:
            return ';'.join(map(lambda v: v.isoformat()[:16], values))
        return ''
