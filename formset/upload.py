import mimetypes
import os
import tempfile
from pathlib import Path

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.core.signing import get_cookie_signer
from django.http.response import HttpResponseBadRequest, JsonResponse

THUMBNAIL_MAX_HEIGHT = 200
THUMBNAIL_MAX_WIDTH = 350
UPLOAD_TEMP_DIR = Path(default_storage.base_location) / 'upload_temp'


def get_thumbnail_path(image_path, image_height=THUMBNAIL_MAX_HEIGHT):
    image_path = Path(image_path)
    thumbnail_name = f'{image_path.stem}_h{image_height}{image_path.suffix}'
    return image_path.with_name(thumbnail_name)


def thumbnail_image(storage, image_path, image_height=THUMBNAIL_MAX_HEIGHT):
    try:
        from PIL import Image, ImageOps

        image = Image.open(image_path)
    except Exception:
        return staticfiles_storage.url('formset/icons/file-picture.svg')
    else:
        height = int(image_height)
        width = int(round(image.width * height / image.height))
        width, height = min(width, THUMBNAIL_MAX_WIDTH), min(height, THUMBNAIL_MAX_HEIGHT)
        thumb = ImageOps.fit(ImageOps.exif_transpose(image), (width, height))
        thumbnail_path = get_thumbnail_path(image_path, image_height)
        thumb.save(thumbnail_path)
        return storage.url(thumbnail_path.relative_to(storage.location))


def split_mime_type(content_type):
    try:
        return content_type.split('/')
    except (AttributeError, ValueError):
        return "application", "octet-stream"


def file_icon_url(mime_type, sub_type):
    if mime_type in ['audio', 'font', 'video']:
        return staticfiles_storage.url(f'formset/icons/file-{mime_type}.svg')
    if mime_type == 'application' and sub_type in ['zip', 'pdf']:
        return staticfiles_storage.url(f'formset/icons/file-{sub_type}.svg')
    return staticfiles_storage.url('formset/icons/file-unknown.svg')


def get_file_info(field_file):
    if not field_file:
        return None
    file_path = Path(field_file.path)
    content_type, _ = mimetypes.guess_type(file_path)
    mime_type, sub_type = split_mime_type(content_type)
    if mime_type == 'image':
        if sub_type == 'svg+xml':
            thumbnail_url = field_file.url
        else:
            thumbnail_path = get_thumbnail_path(file_path)
            if thumbnail_path.is_file():
                thumbnail_url = field_file.storage.url(thumbnail_path.relative_to(field_file.storage.location))
            else:
                thumbnail_url = thumbnail_image(field_file.storage, file_path)
    else:
        thumbnail_url = file_icon_url(mime_type, sub_type)
    name = '.'.join(file_path.name.split('.')[1:])
    if file_path.is_file():
        download_url = field_file.url
        file_size = depict_size(field_file.size)
    else:
        download_url = 'javascript:void(0);'
        thumbnail_url = staticfiles_storage.url('formset/icons/file-missing.svg')
        file_size = '–'
    return {
        'content_type': content_type,
        'name': name,
        'path': field_file.name,
        'download_url': download_url,
        'thumbnail_url': thumbnail_url,
        'size': file_size,
    }


class FileUploadMixin:
    """
    Add this mixin to any Django View class using a form which accept file uploads through
    the provided widget :class:`formset.widgets.UploadedFileInput`.
    """
    filename_max_length = 250

    def post(self, request, **kwargs):
        if request.content_type == 'multipart/form-data' and 'temp_file' in request.FILES and 'image_height' in request.POST:
            return self._receive_uploaded_file(request.FILES['temp_file'], request.POST['image_height'])
        return super().post(request, **kwargs)

    def _receive_uploaded_file(self, file_obj, image_height=None):
        """
        Iterate over all uploaded files.
        """
        if not file_obj:
            return HttpResponseBadRequest(f"File upload failed for '{file_obj.name}'.")
        signer = get_cookie_signer(salt='formset')

        # copy uploaded file into temporary clipboard inside the default storage location
        UPLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        file_path = Path(file_obj.name)
        fh, temp_path = tempfile.mkstemp(suffix=file_path.suffix, prefix=f'{file_path.stem}.', dir=UPLOAD_TEMP_DIR)
        for chunk in file_obj.chunks():
            os.write(fh, chunk)
        os.close(fh)
        assert default_storage.size(temp_path) == file_obj.size
        relative_path = Path(temp_path).relative_to(default_storage.location)
        download_url = default_storage.url(relative_path)

        # dict returned by the form on submission
        mime_type, sub_type = split_mime_type(file_obj.content_type)
        if mime_type == 'image':
            if sub_type == 'svg+xml':
                thumbnail_url = download_url
            else:
                thumbnail_url = thumbnail_image(default_storage, temp_path, image_height=image_height)
        else:
            thumbnail_url = file_icon_url(mime_type, sub_type)
        file_handle = {
            'upload_temp_name': signer.sign(relative_path),
            'content_type': f'{mime_type}/{sub_type}',
            'content_type_extra': file_obj.content_type_extra,
            'name': file_obj.name[:self.filename_max_length],
            'download_url': download_url,
            'thumbnail_url': thumbnail_url,
            'size': file_obj.size,
        }
        return JsonResponse(file_handle)


def depict_size(size):
    if size > 1048576:
        return '{:.1f}MB'.format(size / 1048576)
    if size > 10240:
        return '{:.0f}kB'.format(size / 1024)
    return str(size)
