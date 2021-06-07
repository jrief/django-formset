from django.db import models


class PayloadModel(models.Model):
    data = models.JSONField()


class ChoicesModel(models.Model):
    tenant = models.PositiveSmallIntegerField()

    label = models.CharField(
        "Choice",
        max_length=50,
    )

    class Meta:
        unique_together = ['tenant', 'label']

    def __str__(self):
        return self.label
