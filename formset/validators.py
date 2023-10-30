from django.core.validators import RegexValidator
from django.utils.regex_helper import _lazy_re_compile
from django.utils.translation import gettext_lazy as _

phone_number_validator = RegexValidator(
    _lazy_re_compile(r'^\+\d{3,15}$'),
    message=_("Enter a valid phone number."),
    code="invalid",
)
