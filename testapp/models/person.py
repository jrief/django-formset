from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models

from .poll import OpinionModel


class PersonModel(models.Model):
    class Gender(models.TextChoices):
        Female = 'female'
        Male = 'male'

    class Continent(models.IntegerChoices):
        America = 1
        Europe = 2
        Asia = 3
        Africa = 4
        Australia = 5
        Oceania = 6
        Antartica = 7

    full_name = models.CharField(
        verbose_name="Full Name",
        max_length=50,
    )
    avatar = models.FileField(
        upload_to='images',
        blank=True,
    )
    gender = models.CharField(
        verbose_name="Gender",
        choices=Gender.choices,
        max_length=10,
        blank=False,
        default=None,
    )
    birth_date = models.DateField(
        verbose_name="Birth Date",
    )
    opinion = models.ForeignKey(
        OpinionModel,
        verbose_name="Opinion",
        on_delete=models.CASCADE,
        related_name='persons',
    )
    opinions = models.ManyToManyField(
        OpinionModel,
        verbose_name="Opinions",
        related_name='person_groups',
    )
    continent = models.IntegerField(
        verbose_name="Continent",
        choices=Continent.choices,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )
    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )
    weight = models.IntegerField(
        verbose_name="Weight in kg",
        validators=[
            MinValueValidator(42, message="You are too lightweight."),
            MaxValueValidator(95, message="You are too obese."),
        ],
        blank=True,
        null=True,
    )
    height = models.FloatField(
        verbose_name="Height in meters",
        validators=[
            MinValueValidator(1.45, message="You are too short."),
            MaxValueValidator(1.95, message="You are too tall."),
        ],
        blank=True,
        null=True,
    )
    annotation = models.TextField(
        verbose_name="Annotation",
        blank=True,
        null=True,
    )

    class Meta:
        app_label = "testapp"
        verbose_name = "Person"
        verbose_name_plural = "Persons"

    def __str__(self):
        return self.full_name


class UserContact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts',
    )
    phone_number = models.CharField(
        verbose_name="Phone Number",
        max_length=25,
        validators=[
            RegexValidator(
                regex=r'^\+?[ 0-9.\-]{4,25}$',
                message="Phone number have 4-25 digits and may start with '+'.",
            ),
        ],
        blank=True,
        null=True,
    )
