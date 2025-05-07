from django.forms.fields import JSONField

from formset.widgets.richtext import RichTextarea


class RichTextField(JSONField):
    """
    Use this field to store rich text content in JSON.
    """
    def __init__(self, widget=None, *args, **kwargs):
        if isinstance(widget, RichTextarea):
            widget.attrs['use_json'] = True
        else:
            widget = RichTextarea(attrs={'use_json': True})
        super().__init__(widget=widget, *args, **kwargs)

    def to_python(self, value):
        """Return a dict as required by TipTap."""
        if value in self.empty_values:
            return {'type': 'doc', 'content': []}
        return super().to_python(value)

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValueError("Invalid value: Expected a dictionary.")
        if value.get('type') != 'doc' or not isinstance(value.get('content'), list):
            raise ValueError("Invalid value: Expected a document with content.")
