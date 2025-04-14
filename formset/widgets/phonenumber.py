from django.forms.widgets import TextInput


class PhoneNumberInput(TextInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.update({
            'is': 'django-phone-number',
            'pattern': r'\+\d{3,16}',  # E.164 format
        })
