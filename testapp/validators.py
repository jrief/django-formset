from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.exceptions import ValidationError


def validate_password(value):
    pwhasher = PBKDF2PasswordHasher()
    if not pwhasher.verify(value, 'pbkdf2_sha256$216000$salt$NBY9WN4TPwv2NZJE57BRxccYp0FpyOu82J7RmaYNgQM='):
        raise ValidationError("The password is wrong.")
