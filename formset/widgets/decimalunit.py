from django.forms.widgets import TextInput


class DecimalUnitInput(TextInput):
    def __init__(self, decimal_places, prefix=None, postfix=None, attrs=None):
        super().__init__(attrs)
        self.attrs.update({
            'is': 'django-decimal-unit',
            'decimal-places': decimal_places,
        })
        if prefix is not None:
            self.attrs['prefix'] = prefix
        if postfix is not None:
            self.attrs['postfix'] = postfix
