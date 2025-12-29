from django.forms import forms, fields

from formset.widgets import UploadedFileInput


class UploadForm(forms.Form):
    """
    This form shows how to use Django's ``django.db.models.FileField`` and/or
    ``django.db.models.ImageField``. It allows users to pre-upload a file before form submission.
    """
    avatar = fields.FileField(
        label="Avatar",
        widget=UploadedFileInput(attrs={'accept': 'image/jpeg, image/png'}),
        required=True,
        help_text="Upload avatar image in JPEG or PNG format.",
    )
