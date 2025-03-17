from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models


class ProductModel(models.Model):
    title = models.CharField(
        verbose_name="Title",
        max_length=50,
    )
    price = models.DecimalField(
        verbose_name='Price',
        decimal_places=2,
        max_digits=10,
    )
    properties = models.JSONField(default=dict)
    extra_data = models.JSONField(default=dict)
    last_modified_at = models.DateTimeField(
        auto_now=True,
    )
    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )
