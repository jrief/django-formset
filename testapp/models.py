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
