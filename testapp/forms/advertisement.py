from django.forms import models

from testapp.models import AdvertisementModel


class AdvertisementForm(models.ModelForm):
    """
    This Form shows how to edit rich text.

    .. code-block:: python

        class RichTextForm(forms.Form):
            description = fields.CharField(…)

    """
    # prefix = "advertisement"

    class Meta:
        model = AdvertisementModel
        fields = '__all__'
