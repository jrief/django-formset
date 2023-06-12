from django.db import models

from formset.richtext.fields import RichTextField


class BlogModel(models.Model):
    text = RichTextField()

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )
