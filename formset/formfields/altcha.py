import base64
import datetime
import json

from altcha import create_challenge, verify_solution, Challenge, Payload, Solution

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.forms.fields import Field
from django.forms.widgets import Widget


class AltchaField(Field):
    widget = type('AltchaWidget', (Widget,), {'template_name': 'formset/default/widgets/altcha.html'})()
    timeout = 600

    def prepare_value(self, value):
        challenge = create_challenge(
            algorithm='PBKDF2/SHA-256',
            expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=self.timeout),
            cost=5_000,
            hmac_secret=settings.SECRET_KEY,
        )
        return json.dumps(challenge.to_dict() if challenge else '{}')

    def validate(self, value):
        if value in self.empty_values:
            raise ValidationError(self.error_messages['required'], code='required')
        d = json.loads(base64.b64decode(value).decode())
        payload = Payload(Challenge.from_dict(d['challenge']), Solution.from_dict(d['solution']))
        result = verify_solution(payload, hmac_secret=settings.SECRET_KEY)
        if not result.verified:
            raise ValidationError(result.error, code='invalid')
        key = 'altcha_nonce:{}'.format(d['challenge']['parameters']['nonce'])
        if cache.get(key):
            raise ValidationError("This challenge has already been used.", code='invalid')
        cache.set(key, True, timeout=self.timeout)
