from django.db import models
from django.db.models.expressions import F, Func, Value
from django.db.models.fields import BooleanField, CharField, DateField, DecimalField, TextField, DateTimeField
from django.db.models.fields.files import FileField
from django.db.models.fields.generated import GeneratedField
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.functions import Concat

from formset.modelfields.richtext import RichTextField


class FeeModel(models.Model):
    name = CharField(
        max_length=100,
    )
    free = BooleanField(
        verbose_name="Free of Charge",
        default=False,
    )
    amount = DecimalField(
        verbose_name="Amount",
        decimal_places=2,
        max_digits=10,
    )


class EventSeriesModel(models.Model):
    created_by = CharField(
        editable=False,
        max_length=40,
        db_index=True,
    )
    name = CharField(
        verbose_name="Name of Event",
        max_length=100,
    )
    slug = CharField(
        max_length=50,
    )
    lead = RichTextField(
        verbose_name="Lead Text",
        max_length=500,
    )
    image = FileField(
        verbose_name="Lead Image",
        upload_to='eventseries',
        blank=True,
        null=True,
    )
    fees = ManyToManyField(
        FeeModel,
        verbose_name="Entrance Fees",
    )
    registration_deadline = DateField(
        verbose_name="Registration Deadline",
        null=True,
    )

    class Meta:
        verbose_name = verbose_name_plural = "Event-Series"

    def __str__(self):
        return self.name


class EventOccurrenceModel(models.Model):
    event_series = ForeignKey(
        EventSeriesModel,
        on_delete=models.CASCADE,
        related_name='occurrences',
    )
    venue = CharField(
        verbose_name="Venue",
        max_length=100,
    )
    begin = DateTimeField()
    until = DateTimeField()
    # begin_end = GeneratedField(
    #     verbose_name="Begin- and end",
    #     expression=Concat(
    #         Func(
    #             Value('%Y-%m-%dT%H:%M;'),
    #             F('_begin'),
    #             function='strftime',
    #             output_field=CharField(),
    #         ),
    #         Func(
    #             Value('%Y-%m-%dT%H:%M'),
    #             F('_end'),
    #             function='strftime',
    #             output_field=CharField(),
    #         ),
    #     ),
    #     output_field=CharField(),
    #     db_persist=False,
    # )

    class Meta:
        verbose_name = "Event Occurrence"
        verbose_name_plural = "Event Occurrence"
        ordering = ['begin']

    def __str__(self):
        return self.event_series.name
