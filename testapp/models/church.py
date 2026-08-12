from django.db import models

from formset.modelfields import GeoMapField, RichTextField


class ChurchModel(models.Model):
    map = GeoMapField()
    body = RichTextField()

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )
