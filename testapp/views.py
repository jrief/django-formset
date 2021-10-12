from django.urls import reverse_lazy

from formset.views import FormView

from testapp.forms import SubscribeForm
from testapp.sampledata import sample_subscribe_data


class SubscribeFormView(FormView):
    form_class = SubscribeForm
    success_url = reverse_lazy('form_data_valid')
    initial = sample_subscribe_data
