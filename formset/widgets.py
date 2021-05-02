import os

from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from django.core.signing import get_cookie_signer
from django.forms.widgets import FileInput


class UploadedFileInput(FileInput):
    """
    Widget to be used as a replacement for fields of type :class:`django.forms.fields.FileField`
    and :class:`django.forms.fields.ImageField`.
    It converts the submitted POST data to reference the already uploaded file in the directory
    configured for temporary uploads.
    """
    template_name = 'formset/default/widgets/file.html'

    def format_value(self, value):
        return value

    def value_from_datadict(self, data, files, name):
        signer = get_cookie_signer(salt='formset')
        if handle := next(iter(data.get(name, ())), None):
            upload_temp_name = signer.unsign(handle['upload_temp_name'])
            file = open(default_storage.path(upload_temp_name))
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            files[name] = UploadedFile(
                file=file, name=handle['name'], size=size, content_type=handle['content_type'],
                content_type_extra=handle['content_type_extra'],
            )
        return files.get(name)
