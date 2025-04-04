import json

from django.forms.fields import Field

from formset.richtext.widgets import RichTextarea


class RichTextField(Field):
    """
    Use this field to embed a rich text content into a JSONField when used in combination with a ``fields_map``.
    """
    def __init__(self, widget=None, *args, **kwargs):
        if isinstance(widget, RichTextarea):
            widget.attrs['use_json'] = True
        else:
            widget = RichTextarea(attrs={'use_json': True})
        super().__init__(widget=widget, *args, **kwargs)

    def to_python(self, value):
        """Return a dict as required by TipTap."""
        if isinstance(value, dict):
            return value
        if value in self.empty_values:
            return {'type': 'doc', 'content': []}
        try:
            return json.loads(value)
        except ValueError:
            return {'type': 'doc', 'content': [{'type': 'text', 'text': str(value)}]}

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValueError("Invalid value: expected a dictionary.")
        if value.get('type') != 'doc' or not isinstance(value.get('content'), list):
            raise ValueError("Invalid value: expected a document with content.")
