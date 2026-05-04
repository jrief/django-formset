from django.db import models

from formset.modelfields import RichTextField


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
    extra_data = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Gallery"
        verbose_name_plural = "Galleries"
        constraints = [models.UniqueConstraint(fields=['name', 'created_by'], name='unique_name')]

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
    position = models.PositiveIntegerField(
        editable=False,
        default=0,
    )

    class Meta:
        ordering = ['position']
        indexes = [models.Index(fields=['position'], name='image_position_idx')]
