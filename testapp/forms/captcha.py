from django.forms import fields, forms

from formset.formfields.altcha import AltchaField


class CaptchaForm(forms.Form):
    """
    How to use ``ALTCHA``.
    """

    email = fields.EmailField(
        initial='joe@example.com',
        help_text="Subscribe with your email address.",
    )
    captcha_token = AltchaField()
