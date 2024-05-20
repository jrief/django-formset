from django.db import models

from .reporter import Reporter


class Article(models.Model):
    pub_date = models.DateField()
    headline = models.CharField(max_length=200)
    content = models.TextField()
    reporter = models.ForeignKey(
        Reporter,
        on_delete=models.CASCADE,
    )
    teaser = models.FileField(
        upload_to='images',
        blank=True,
    )
    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )

    def __str__(self):
        return self.headline
