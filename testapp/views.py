from django.urls import reverse_lazy

from formset.views import FormsetView

from testapp.forms import SubscribeForm


class SubscribeFormView(FormsetView):
    form_class = SubscribeForm
    success_url = reverse_lazy('form_data_valid')


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
