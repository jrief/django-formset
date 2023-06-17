from django.db import models


class Annotation(models.Model):
    content = models.CharField(max_length=200)

    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )

    def __str__(self):
        return self.content
