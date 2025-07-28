from django.forms.widgets import NumberInput


class DecimalUnitInput(NumberInput):
    def __init__(self, prefix=None, suffix=None, fixed_decimal_places=False, attrs=None):
        super().__init__(attrs)
        self.attrs.update({
            'is': 'django-decimal-unit',
        })
        if prefix is not None:
            self.attrs['prefix'] = prefix
        if suffix is not None:
            self.attrs['suffix'] = suffix
        if fixed_decimal_places:
            self.attrs['fixed-decimal-places'] = True
