from django.urls import reverse_lazy
from django.utils.timezone import datetime

from formset.views import FormView

from testapp.forms import SubscribeForm


class SubscribeFormView(FormView):
    form_class = SubscribeForm
    success_url = reverse_lazy('form_data_valid')


sample_subscribe_data = {
    'first_name': "John",
    'last_name': "Doe",
    'sex': 'm',
    'email': 'john.doe@example.org',
    'subscribe': True,
    'phone': '+1 234 567 8900',
    'birth_date': datetime(year=1966, month=7, day=9),
    'continent': 'eu',
    'available_transportation': ['foot', 'taxi'],
    'preferred_transportation': 'car',
    'used_transportation': ['foot', 'bike', 'car', 'train'],
    'height': 1.82,
    'weight': 81,
    'traveling': ['bike', 'train'],
    'notifyme': ['email', 'sms'],
    'annotation': "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    'password': 'secret',
}
