from django.db import models


class Reporter(models.Model):
    full_name = models.CharField(max_length=70)

    def __str__(self):
        return self.full_name


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
