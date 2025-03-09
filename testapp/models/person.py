from django.conf import settings
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


class UserContact(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts',
    )

    phone_number = models.CharField(
        verbose_name="Phone Number",
        max_length=25,
        blank=True,
        null=True,
    )
