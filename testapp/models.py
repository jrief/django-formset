from django.db import models


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


class PersonModel(models.Model):
    full_name = models.CharField(
        verbose_name="Full Name",
        max_length=50,
    )

    avatar = models.FileField(
        upload_to='images',
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
