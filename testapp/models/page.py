from django.db import models

from testapp.models.reporter import Reporter


class PageModel(models.Model):
    title = models.CharField(
        verbose_name="Page Title",
        max_length=100,
    )
    slug = models.SlugField(
        verbose_name="Page Slug",
        unique=True,
        null=True,
    )
    reporter = models.ForeignKey(
        Reporter,
        on_delete=models.CASCADE,
        verbose_name="Reporter",
        related_name='pages',
    )
    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/pages/{self.slug}/"
