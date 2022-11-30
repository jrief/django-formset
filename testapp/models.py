from django.conf import settings
from django.db import models

from formset.fields import SortableManyToManyField
from formset.richtext.fields import RichTextField


class PayloadModel(models.Model):
    data = models.JSONField()

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )


class OpinionModel(models.Model):
    tenant = models.PositiveSmallIntegerField()

    label = models.CharField(
        "Opinion",
        max_length=50,
    )

    class Meta:
        unique_together = ['tenant', 'label']

    def __str__(self):
        return self.label

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.label}">'


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


class PollModel(models.Model):
    weighted_opinions = SortableManyToManyField(
        OpinionModel,
        through='testapp.WeightedOpinion',
        verbose_name="Weighted Opinions",
    )

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )


class WeightedOpinion(models.Model):
    poll = models.ForeignKey(
        PollModel,
        on_delete=models.CASCADE,
    )

    opinion = models.ForeignKey(
        OpinionModel,
        on_delete=models.CASCADE,
    )

    weight = models.BigIntegerField(
        "Weighted Opinion",
        default=0,
        db_index=True,
    )

    class Meta:
        ordering = ['weight']

    def __repr__(self):
        return f'<{self.__class__.__name__}: [{self.weight}] "{self.opinion.label}">'


class ExtendUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='extend_user',
    )

    phone_number = models.CharField(
        verbose_name="Phone Number",
        max_length=25,
        blank=True,
        null=True,
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


class AdvertisementModel(models.Model):
    text = RichTextField()

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )


class County(models.Model):
    state = models.CharField(
        verbose_name="State",
        max_length=2,
        db_index=True,
    )

    state_name = models.CharField(
        verbose_name="State Name",
        max_length=20,
    )

    county_name = models.CharField(
        verbose_name="State Name",
        max_length=30,
    )

    class Meta:
        ordering = ['state_name', 'county_name']

    def __str__(self):
        return f"{self.county_name} ({self.state})"
