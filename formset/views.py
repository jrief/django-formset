import json

from django.http import JsonResponse
from django.utils.encoding import force_str
from django.views.generic import FormView


class FormsetViewMixin:
    def post(self, request, **kwargs):
        if request.content_type == 'application/json':
            request_data = json.loads(request.body)
            form = self.form_class(data=request_data[self.form_class.name])
            if form.is_valid():
                return JsonResponse({'success_url': force_str(self.success_url)})
            else:
                return JsonResponse({form.name: form.errors}, status=422)
        return super().post(request, **kwargs)


class FormsetView(FormsetViewMixin, FormView):
    pass
