from django.forms import forms, fields

from formset.widgets import UploadedFileInput


class UploadForm(forms.Form):
    """
    This form shows how to use Django's ``django.db.models.FileField`` and/or
    ``django.db.models.ImageField``. It allows us to visually upload a file, which means that the
    uploaded payload is pre-submitted and a thumbnailed depiction is rendered. Since the uploaded
    file already waits in a temporary location on the server, the final form submission also is a
    lot faster.

    .. code-block:: python

        class UploadForm(forms.Form):
            avatar = fields.FileField(
                label="Avatar",
                widget=UploadedFileInput,
                required=True,
            )

    In combination with our webcomponent ``<django-formset>``, using the widget
    ``UploadedFileInput`` is mandatory for fields of type ``FileField`` or ``ImageField``.
    This is because uploading the payload is separated from its form submission.
    """
    avatar = fields.FileField(
        label="Avatar",
        widget=UploadedFileInput,
        required=True,
    )
