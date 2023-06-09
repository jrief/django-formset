from django.db import models
from formset.fields import SortableManyToManyField


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
