import os

from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from django.core.signing import get_cookie_signer
from django.forms.widgets import FileInput
from django.utils.datastructures import MultiValueDict


class UploadedFileInput(FileInput):
    """
    Class to be mixed into class inheriting from :class:`django.forms.widgets.FileInput`.
    It converts to submitted POST data to reference the already uploaded file in the
    directory configured for temporary uploads.
    """
    template_name = 'formset/default/widgets/file.html'

    def value_from_datadict(self, data, files, name):
        signer = get_cookie_signer(salt='formset')
        data = MultiValueDict(data)
        for handle in data.pop(name):
            upload_temp_name = signer.unsign(handle['upload_temp_name'])
            file = open(default_storage.path(upload_temp_name))
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            files[name] = UploadedFile(
                file=file, name=handle['name'], size=size, content_type=handle['content_type'],
                content_type_extra=handle['content_type_extra'])
        return files.get(name)
