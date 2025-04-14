from django.forms.widgets import TextInput


class SlugInput(TextInput):
    def __init__(self, populate_from, attrs=None):
        super().__init__(attrs)
        self.attrs.update({
            'is': 'django-slug',
            'pattern': r'[\-a-zA-Z0-9_]+',
            'populate-from': populate_from,
        })
