from django.db import models

from formset.fields import SortableManyToManyField


class PayloadModel(models.Model):
    data = models.JSONField()


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
