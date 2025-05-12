from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.forms import fields
from django.utils.translation import gettext_lazy as _

from formset.widgets import DateRangePicker, DateTimeRangePicker


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
            raise ValidationError(
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
            if all(isinstance(v, (date, datetime)) for v in values):
                return ';'.join(map(lambda v: f'{v.isoformat()[:10]}T00:00', values))
            if all(isinstance(v, str) for v in values):
                return ';'.join(map(lambda v: f'{v[:10]}T00:00', values))
        return ''


class DateTimeRangeField(DateRangeField):
    base_field = fields.DateTimeField

    def __init__(self, **kwargs):
        kwargs.setdefault('widget', DateTimeRangePicker())
        super().__init__(**kwargs)

    def prepare_value(self, values):
        if isinstance(values, (list, tuple)) and len(values) == 2:
            if all(isinstance(v, (date, datetime)) for v in values):
                return ';'.join(map(lambda v: v.isoformat()[:16], values))
            if all(isinstance(v, str) for v in values):
                return ';'.join(map(lambda v: v[:16], values))
        return ''
