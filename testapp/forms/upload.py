from django.forms import forms, fields

from formset.widgets import UploadedFileInput


class UploadForm(forms.Form):
    """
    This form shows how to use the Django ``FileField`` and/or ``ImageField``. In combination with
    ``<django-formset>`` using the widget ``UploadedFileInput`` is mandatory in order to separate
    file uploading from form submission.
    """
    avatar = fields.FileField(
        label="Avatar",
        widget=UploadedFileInput,
        required=True,
    )
