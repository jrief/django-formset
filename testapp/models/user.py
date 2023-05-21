from django.db import models
from django.utils import timezone


class User(models.Model):
    """
    We fake the user model for testing and documentation
    """
    username = models.CharField(
        "Username",
        max_length=150,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    first_name = models.CharField("First name", max_length=150, blank=True)
    last_name = models.CharField("Last name", max_length=150, blank=True)
    email = models.EmailField("Email address", blank=True)
    is_staff = models.BooleanField(
        "Staff status",
        default=False,
        help_text="Designates whether the user can log into this admin site.",
    )
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text="Designates whether this user should be treated as active."
    )
    date_joined = models.DateTimeField("date joined", default=timezone.now)
    is_superuser = models.BooleanField(
        "superuser status",
        default=False,
        help_text="Designates that this user has all permissions without explicitly assigning them."
    )

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )

    def __str__(self):
        return self.username


class ExtendUser(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='extend_user',
        primary_key=True,
    )

    phone_number = models.CharField(
        verbose_name="Phone Number",
        max_length=25,
        blank=True,
        null=True,
    )
