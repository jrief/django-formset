from django.db import models


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

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/pages/{self.slug}/"
