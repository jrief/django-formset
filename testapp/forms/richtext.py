from django.forms import fields, forms

from formset.widgets import RichTextArea


class RichTextForm(forms.Form):
    """
    This Form shows how to edit rich text.

    .. code-block:: python

        class RichTextForm(forms.Form):
            description = fields.CharField(…)

    """

    description = fields.JSONField(
        label="Description",
        widget=RichTextArea,
    )
