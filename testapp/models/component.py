from django.db import models


class Component(models.Model):
    type = models.CharField(
        max_length=16,
    )
    created_by = models.CharField(
        editable=False,
        max_length=40,
    )
    context = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Component"
        verbose_name_plural = "Components"
        constraints = [models.UniqueConstraint(fields=['type', 'created_by'], name='unique_type')]

    def __str__(self):
        return self.type
