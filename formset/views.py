import json
import os
import tempfile

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import default_storage
from django.core.signing import get_cookie_signer
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.utils.encoding import force_str
from django.views.generic import FormView


class FormsetViewMixin:
    upload_temp_dir = default_storage.base_location / 'upload_temp'
    filename_max_length = 50
    thumbnail_max_height = 200

    def post(self, request, **kwargs):
        if request.content_type == 'application/json':
            return self._handle_form_data(request.body)
        if request.content_type == 'multipart/form-data':
            return self._receive_uploaded_file(request.FILES.get('temp_file'), request.POST.get('image_height'))
        return super().post(request, **kwargs)

    def _handle_form_data(self, form_data):
        form_data = json.loads(form_data)
        form = self.form_class(data=form_data[self.form_class.name])
        if form.is_valid():
            return JsonResponse({'success_url': force_str(self.success_url)})
        else:
            return JsonResponse({form.name: form.errors}, status=422)

    def _receive_uploaded_file(self, file_obj, image_height=None):
        """
        Iterate over all uploaded files.
        """
        if not file_obj:
            return HttpResponseBadRequest(f"File upload failed for '{file_obj.name}'.")
        signer = get_cookie_signer(salt='formset')

        # copy uploaded file into temporary clipboard inside the default storage location
        if not os.path.exists(self.upload_temp_dir):
            os.makedirs(self.upload_temp_dir)
        prefix, ext = os.path.splitext(file_obj.name)
        fh, temp_path = tempfile.mkstemp(suffix=ext, prefix=prefix + '.', dir=self.upload_temp_dir)
        for chunk in file_obj.chunks():
            os.write(fh, chunk)
        os.close(fh)
        relative_path = os.path.relpath(temp_path, default_storage.location)
        assert default_storage.size(relative_path) == file_obj.size

        # dict returned by the form on submission
        mime_type, sub_type = file_obj.content_type.split('/')
        if mime_type == 'image':
            thumbnail_url = self._thumbnail_image(temp_path, image_height)
        else:
            thumbnail_url = self._file_icon_url(file_obj.content_type)
        file_handle = {
            'upload_temp_name': signer.sign(relative_path),
            'content_type': file_obj.content_type,
            'content_type_extra': file_obj.content_type_extra,
            'name': file_obj.name[:self.filename_max_length],
            'download_url': default_storage.url(relative_path),
            'thumbnail_url': thumbnail_url,
            'size': file_obj.size,
        }
        return JsonResponse(file_handle)

    def _thumbnail_image(self, image_path, image_height):
        try:
            from PIL import Image, ImageOps

            image = Image.open(image_path)
        except Exception:
            return staticfiles_storage.url('formset/icons/file-picture.pdf')
        else:
            height = int(image_height) if image_height else self.thumbnail_max_height
            height = min(height, self.thumbnail_max_height)
            size = int(round(image.width * height / image.height)), height
            thumb = ImageOps.fit(image, size)
            base, ext = os.path.splitext(image_path)
            size = 'x'.join(str(s) for s in size)
            thumb_path = f'{base}_{size}{ext}'
            thumb.save(thumb_path)
            thumb_path = os.path.relpath(thumb_path, default_storage.location)
            return default_storage.url(thumb_path)

    def _file_icon_url(self, content_type):
        mime_type, sub_type = content_type.split('/')
        if mime_type in ['audio', 'font', 'video']:
            return staticfiles_storage.url(f'formset/icons/file-{mime_type}.svg')
        if mime_type == 'application' and sub_type in ['zip', 'pdf']:
            return staticfiles_storage.url(f'formset/icons/file-{sub_type}.svg')
        return staticfiles_storage.url('formset/icons/file-unknown.svg')


class FormsetView(FormsetViewMixin, FormView):
    pass
