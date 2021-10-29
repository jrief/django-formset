from django.forms import forms, fields

from formset.widgets import UploadedFileInput


class UploadForm(forms.Form):
    avatar = fields.FileField(
        label="Avatar",
        widget=UploadedFileInput,
        required=True,
    )
