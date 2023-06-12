from django.conf import settings
from django.db import models

from .article import Article, Reporter
from .annotation import Annotation
from .company import Company, Department, Team
from .county import County, CountyUnnormalized, State
from .blog import BlogModel
from .poll import OpinionModel, PollModel, WeightedOpinion
from .user import ExtendUser, User


class PayloadModel(models.Model):
    data = models.JSONField()

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )


class PersonModel(models.Model):
    full_name = models.CharField(
        verbose_name="Full Name",
        max_length=50,
    )

    avatar = models.FileField(
        upload_to='images',
        blank=True,
    )

    class Gender(models.TextChoices):
        Female = 'female'
        Male = 'male'

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

    class Continent(models.IntegerChoices):
        America = 1
        Europe = 2
        Asia = 3
        Africa = 4
        Australia = 5
        Oceania = 6
        Antartica = 7

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
