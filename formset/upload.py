import mimetypes
from pathlib import Path

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.core.files.uploadhandler import UploadFileException
from django.core.signing import get_cookie_signer
from django.http.response import HttpResponseBadRequest, JsonResponse

FILENAME_MAX_LENGTH = 250
THUMBNAIL_MAX_HEIGHT = 200
THUMBNAIL_MAX_WIDTH = 350
UPLOAD_TEMP_DIR = Path('upload_temp')


def get_thumbnail_path(image_path, image_height=THUMBNAIL_MAX_HEIGHT):
    image_path = Path(image_path)
    thumbnail_name = f'{image_path.stem}_h{image_height}{image_path.suffix}'
    return image_path.with_name(thumbnail_name)


def thumbnail_image(storage, image_path, image_height=THUMBNAIL_MAX_HEIGHT):
    try:
        from PIL import Image, ImageOps

        image = Image.open(storage.path(image_path))
    except Exception:
        return staticfiles_storage.url('formset/icons/file-picture.svg')
    else:
        height = int(image_height)
        width = int(round(image.width * height / image.height))
        width, height = min(width, THUMBNAIL_MAX_WIDTH), min(height, THUMBNAIL_MAX_HEIGHT)
        thumb = ImageOps.fit(ImageOps.exif_transpose(image), (width, height))
        thumbnail_path = get_thumbnail_path(storage.path(image_path), image_height)
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
    try:
        file_path = Path(field_file.path)
    except (ValueError, TypeError):
        return
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


def receive_uploaded_file(file_obj, image_height=None):
    """
    Accept an uploaded file and return a handle to it.
    """
    if not file_obj:
        raise UploadFileException(f"File upload failed.")
    signer = get_cookie_signer(salt='formset')

    temp_path = default_storage.save(UPLOAD_TEMP_DIR / file_obj.name, file_obj)
    assert default_storage.size(temp_path) == file_obj.size
    download_url = default_storage.url(temp_path)

    # dict returned by the form on submission
    mime_type, sub_type = split_mime_type(file_obj.content_type)
    if mime_type == 'image':
        if sub_type == 'svg+xml':
            thumbnail_url = download_url
        else:
            thumbnail_url = thumbnail_image(default_storage, temp_path, image_height=image_height)
    else:
        thumbnail_url = file_icon_url(mime_type, sub_type)
    return {
        'upload_temp_name': signer.sign(temp_path),
        'content_type': f'{mime_type}/{sub_type}',
        'content_type_extra': file_obj.content_type_extra,
        'name': file_obj.name[:FILENAME_MAX_LENGTH],
        'download_url': download_url,
        'thumbnail_url': thumbnail_url,
        'size': file_obj.size,
    }


class FileUploadMixin:
    """
    Add this mixin to any Django View class using a form which accept file uploads through
    the provided widget :class:`formset.widgets.UploadedFileInput`.
    """
    def post(self, request, **kwargs):
        if request.content_type == 'multipart/form-data' and 'temp_file' in request.FILES and 'image_height' in request.POST:
            try:
                return JsonResponse(receive_uploaded_file(request.FILES['temp_file'], request.POST['image_height']))
            except Exception as e:
                return HttpResponseBadRequest(str(e))
        return super().post(request, **kwargs)


def depict_size(size):
    if size > 1048576:
        return '{:.1f}MB'.format(size / 1048576)
    if size > 10240:
        return '{:.0f}kB'.format(size / 1024)
    return str(size)
