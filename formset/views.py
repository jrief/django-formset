import json
import os
import tempfile

from django.core.files.storage import default_storage
from django.core.signing import get_cookie_signer
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.utils.encoding import force_str
from django.views.generic import FormView


class FormsetViewMixin:
    upload_temp_dir = default_storage.base_location / 'upload_temp'

    def post(self, request, **kwargs):
        if request.content_type == 'application/json':
            return self.handle_form_data(request.body)
        if request.content_type == 'multipart/form-data':
            return self.receive_uploaded_file(request.FILES.get('temp_file'))
        return super().post(request, **kwargs)

    def handle_form_data(self, form_data):
        form_data = json.loads(form_data)
        form = self.form_class(data=form_data[self.form_class.name])
        if form.is_valid():
            return JsonResponse({'success_url': force_str(self.success_url)})
        else:
            return JsonResponse({form.name: form.errors}, status=422)

    def receive_uploaded_file(self, file_obj):
        """
        Iterate over all uploaded files.
        """
        if not file_obj:
            return HttpResponseBadRequest(f"File upload failed for '{file_obj.name}'.")

        # copy uploaded file into temporary clipboard inside the default storage location
        prefix, ext = os.path.splitext(file_obj.name)
        fh, temp_path = tempfile.mkstemp(suffix=ext, prefix=prefix + '.', dir=self.upload_temp_dir)
        for chunk in file_obj.chunks():
            os.write(fh, chunk)
        os.close(fh)
        relative_path = os.path.relpath(temp_path, default_storage.location)
        assert default_storage.size(relative_path) == file_obj.size

        # dict returned by the form on submission
        signer = get_cookie_signer(salt='formset')
        file_handle = {
            'upload_temp_name': signer.sign(relative_path),
            'content_type': file_obj.content_type,
            'content_type_extra': file_obj.content_type_extra,
            'name': file_obj.name,
            'url': default_storage.url(relative_path),
        }
        return JsonResponse(file_handle)


class FormsetView(FormsetViewMixin, FormView):
    pass
