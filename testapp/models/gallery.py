from django.db import models

from formset.richtext.fields import RichTextField


class Gallery(models.Model):
    name = models.CharField(
        verbose_name="Gallery name",
        max_length=50,
    )
    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )

    class Meta:
        verbose_name = "Gallery"
        verbose_name_plural = "Galleries"
        unique_together = ['name', 'created_by']

    def __str__(self):
        return self.name


class Image(models.Model):
    image = models.FileField(
        upload_to='images',
        blank=True,
    )
    caption = RichTextField(
        blank=True,
        null=True,
    )
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='images',
    )
