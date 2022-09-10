from django.forms import models

<<<<<<< HEAD
from testapp.models import AdvertisementModel


class AdvertisementForm(models.ModelForm):
=======
from formset.widgets import RichTextArea

from testapp.models import PayloadModel


class RichTextForm(models.ModelForm):
>>>>>>> origin/tiptap
    """
    This Form shows how to edit rich text.

    .. code-block:: python

        class RichTextForm(forms.Form):
            description = fields.CharField(…)

    """
    class Meta:
<<<<<<< HEAD
        model = AdvertisementModel
        fields = '__all__'
=======
        model = PayloadModel
        fields = '__all__'
        widgets = {
            'data': RichTextArea,
        }
>>>>>>> origin/tiptap
