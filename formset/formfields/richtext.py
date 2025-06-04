from django.forms.fields import JSONField

from formset.widgets.richtext import RichTextarea


class RichTextField(JSONField):
    """
    Use this field to store rich text content in JSON.
    """
    upload_to = ''
    storage = None

    def __init__(self, widget=None, upload_to=None, storage=None, *args, **kwargs):
        if isinstance(widget, RichTextarea):
            widget.attrs['use_json'] = True
        else:
            widget = RichTextarea(attrs={'use_json': True})
        if upload_to is not None:
            self.upload_to = upload_to
        if storage is not None:
            self.storage = storage
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

    def clean(self, value):
        value = super().clean(value)
        if isinstance(value, dict) and 'content' in value:
            for control_element in self.widget.control_elements:
                control_element.clean_content(self, value['content'])
        return value
