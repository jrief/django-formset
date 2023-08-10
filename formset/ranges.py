from django import forms
from django.core import exceptions
from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _


class BaseRangeField(forms.MultiValueField):
    default_error_messages = {
        'invalid': _("Enter two valid values."),
        'bound_ordering': _("The start of the range must not exceed the end of the range."),
    }

    def __init__(self, widget, **kwargs):
        if 'fields' not in kwargs:
            kwargs['fields'] = [
                self.base_field(required=False),
                self.base_field(required=False),
            ]
        kwargs.setdefault('required', False)
        kwargs.setdefault('require_all_fields', False)
        self.range_kwargs = {}
        if default_bounds := kwargs.pop('default_bounds', None):
            self.range_kwargs = {'bounds': default_bounds}
        super().__init__(widget=widget, **kwargs)

    def prepare_value(self, value):
        lower_base, upper_base = self.fields
        return value

    def compress(self, values):
        if not values:
            return None
        lower, upper = values


class DateRangeField(BaseRangeField):
    default_error_messages = {"invalid": _("Enter two valid dates.")}
    base_field = forms.DateField

    def __init__(self, **kwargs):
        if 'widget' not in kwargs:
            kwargs["widget"] = TextInput(attrs={
                'type': 'regex',
                'pattern': r'^\d{4}-\d{2}-\d{2};\d{4}-\d{2}-\d{2}$',
                'is': 'django-daterangepicker',
            })
        super().__init__(**kwargs)
