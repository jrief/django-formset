import base64
import datetime
import json

from altcha import create_challenge, verify_solution, Challenge, Payload, Solution

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.forms.fields import Field
from django.forms.widgets import Widget
from django.utils.translation import gettext_lazy as _


class AltchaField(Field):
    widget = type('AltchaWidget', (Widget,), {'template_name': 'formset/default/widgets/altcha.html'})()
    timeout = 600
    cost = 10000
    algorithm = 'PBKDF2/SHA-256'
    default_error_messages = {
        'required': _("Verification response is missing."),
        'invalid_signature': _("Invalid solution signature."),
        'invalid_solution': _("Invalid challenge solution."),
        'expired': _("This challenge has expired."),
        'redeemed': _("Challenge solution already redeemed."),
        'invalid': "Invalid",
    }

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop('timeout', self.timeout)
        self.cost = kwargs.pop('cost', self.cost)
        self.algorithm = kwargs.pop('algorithm', self.algorithm)
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        challenge = create_challenge(
            algorithm=self.algorithm,
            expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=self.timeout),
            cost=self.cost,
            hmac_secret=settings.SECRET_KEY,
        )
        return json.dumps(challenge.to_dict() if challenge else '{}')

    def validate(self, value):
        if value in self.empty_values:
            raise ValidationError(self.error_messages['required'], code='required')
        try:
            data = json.loads(base64.b64decode(value).decode())
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValidationError(exc.msg, code='invalid')
        payload = Payload(Challenge.from_dict(data['challenge']), Solution.from_dict(data['solution']))
        result = verify_solution(payload, hmac_secret=settings.SECRET_KEY)
        if result.expired:
            raise ValidationError(self.error_messages['expired'], code='expired')
        if result.invalid_signature:
            raise ValidationError(self.error_messages['invalid_signature'], code='invalid_signature')
        if result.invalid_solution:
            raise ValidationError(self.error_messages['invalid_solution'], code='invalid_solution')
        if result.verified:
            key = 'altcha_nonce:{}'.format(data['challenge']['parameters']['nonce'])
            if cache.get(key):
                raise ValidationError(self.error_messages['redeemed'], code='redeemed')
            cache.set(key, True, timeout=self.timeout)
        else:
            raise ValidationError(result.error, code='invalid')
