import json

from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.utils.encoding import force_text

from forms import SubscribeForm


class SubscribeView(FormView):
    template_name = 'form2.html'
    form_class = SubscribeForm
    success_url = reverse_lazy('form_data_valid')

    def get(self, request, **kwargs):
        if request.is_ajax():
            form = self.form_class(initial=default_subscribe_data)
            return JsonResponse({form.form_name: form.initial})
        return super().get(request, **kwargs)

    def post(self, request, **kwargs):
        assert request.content_type == 'application/json'
        return self.ajax(request)

    def ajax(self, request):
        request_data = json.loads(request.body)
        form = self.form_class(data=request_data[self.form_class.name])
        if form.is_valid():
            return JsonResponse({'success_url': force_text(self.success_url)})
        else:
            return JsonResponse({form.name: form.errors}, status=422)


default_subscribe_data = {
    'first_name': "John",
    'last_name': "Doe",
    'sex': 'm',
    'email': 'john.doe@example.org',
    'phone': '+1 234 567 8900',
    'birth_date': '1975-06-01',
    'continent': 'eu',
    'height': 1.82,
    'weight': 81,
    'traveling': ['bike', 'train'],
    'notifyme': ['email', 'sms'],
    'annotation': "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    'agree': True,
    'password': '',
}
