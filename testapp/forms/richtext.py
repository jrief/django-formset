from django.forms import models

from formset.widgets import RichTextArea

from testapp.models import PayloadModel


class RichTextForm(models.ModelForm):
    """
    This Form shows how to edit rich text.

    .. code-block:: python

        class RichTextForm(forms.Form):
            description = fields.CharField(…)

    """
    class Meta:
        model = PayloadModel
        fields = '__all__'
        widgets = {
            'data': RichTextArea,
        }
