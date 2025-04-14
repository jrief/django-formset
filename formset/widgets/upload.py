import os
import struct
from base64 import b16encode
from datetime import timezone
from pathlib import Path

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.core.signing import get_cookie_signer
from django.forms.widgets import FILE_INPUT_CONTRADICTION, FileInput
from django.utils.timezone import datetime, now


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
        handle = data.get(name)
        if isinstance(handle, (UploadedFile, bool)):
            return handle
        if hasattr(handle, '__iter__'):
            handle = next(iter(handle), None)
        if isinstance(handle, dict):
            if not handle:
                return False  # marked as deleted
            if 'upload_temp_name' not in handle:
                # widget already initialized, mark as Path to bypass ``clean()``-method
                return Path(handle['path'])

            # check if the file type corresponds to the allowed types
            if accept := self.attrs.get('accept'):
                main_type, sub_type = handle['content_type'].split('/')
                try:
                    accepted = [a.strip().split('/') for a in accept.split(',')]
                    for acc_main, acc_sub in accepted:
                        if acc_main == '*' or acc_main == main_type and acc_sub in ['*', sub_type]:
                            break
                    else:
                        # apparently the user has tampered with the content type and bypassed the browser check
                        # hence prevent the temporarily uploaded file from being moved to its final destination
                        return FILE_INPUT_CONTRADICTION
                except ValueError:
                    pass

            # check if the uploaded file has been signed by the server
            signer = get_cookie_signer(salt='formset')
            upload_temp_name = signer.unsign(handle['upload_temp_name'])
            file = default_storage.open(upload_temp_name, 'rb')
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            # create pseudo unique prefix to avoid file name collisions
            epoch = datetime(2022, 1, 1, tzinfo=timezone.utc)
            prefix = b16encode(struct.pack('f', (now() - epoch).total_seconds())).decode('utf-8')
            filename = '.'.join((prefix, handle['name']))
            files[name] = UploadedFile(
                file=file, name=filename, size=size, content_type=handle['content_type'],
                content_type_extra=handle['content_type_extra'],
            )
        return files.get(name)
