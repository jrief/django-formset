from django.forms import fields
from django.utils.translation import gettext_lazy as _

from formset.widgets import DatePicker


class BaseRangeField(fields.MultiValueField):
    default_error_messages = {
        'invalid': _("Enter two valid values."),
        'bound_ordering': _("The start of the range must not exceed the end of the range."),
    }

    def __init__(self, widget, **kwargs):
        kwargs.setdefault('required', True)
        kwargs.setdefault('require_all_fields', kwargs['required'])
        if 'fields' not in kwargs:
            kwargs['fields'] = [
                self.base_field(required=kwargs['required']),
                self.base_field(required=kwargs['required']),
            ]
        self.range_kwargs = {}
        if default_bounds := kwargs.pop('default_bounds', None):
            self.range_kwargs = {'bounds': default_bounds}
        super().__init__(widget=widget, **kwargs)

    def prepare_value(self, values):
        if isinstance(values, (list, tuple)) and len(values) == 2:
            return ';'.join((values[0].isoformat(), values[1].isoformat()))
        return ''

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
        if 'widget' not in kwargs:
            kwargs['widget'] = DatePicker(attrs={
                'type': 'regex',
                'pattern': r'^\d{4}-\d{2}-\d{2};\d{4}-\d{2}-\d{2}$',
                'is': 'django-daterangepicker',
            })
        super().__init__(**kwargs)
