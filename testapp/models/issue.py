from django.db import models
from django.urls import reverse

from testapp.models.reporter import Reporter


class IssueModel(models.Model):
    title = models.CharField(
        verbose_name="Issue Title",
        max_length=100,
    )
    reporter = models.ForeignKey(
        Reporter,
        on_delete=models.CASCADE,
        verbose_name="Reporter",
        related_name='issues',
    )
    created_by = models.CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/pages/{self.id}/"
