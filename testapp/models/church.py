from django.db import models

from formset.modelfields import GeoMapField


class ChurchModel(models.Model):
    map = GeoMapField()

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )
