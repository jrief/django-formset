from django.utils.timezone import datetime
from testapp.models import OpinionModel


sample_subscribe_data = {
    'first_name': "John",
    'last_name': "Doe",
    'gender': 'm',
    'email': 'john.doe@example.org',
    'subscribe': True,
    'phone': '+1 234 567 8900',
    'birth_date': datetime(year=1966, month=7, day=9),
    'continent': 'eu',
    'opinion': lambda: OpinionModel.objects.filter(tenant=1)[8],
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

sample_persona_data = {
    'first_name': "John",
    'last_name': "Doe",
    'gender': 'm',
    'accept': True,
}


sample_selectize_data = {
    'choice': 2,
    'opinion': lambda: OpinionModel.objects.filter(tenant=1)[6],
    'annotation': "Lorem ipsum dolor est",
}
