from django.db import models
from django.urls import reverse

from formset.modelfields.richtext import RichTextField

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
    content = RichTextField(
        verbose_name="Page Content",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('page_detail', kwargs={'slug': self.slug})
