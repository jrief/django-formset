try:
    from django.forms.widgets import TelInput
except ImportError:
    from django.forms.widgets import TextInput as TelInput  # Django<5.2


class PhoneNumberInput(TelInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.update({
            'is': 'django-phone-number',
            'pattern': r'\+\d{3,16}',  # E.164 format
        })
