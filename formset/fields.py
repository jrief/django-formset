from django.core import checks
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import ManyToManyField

from formset.richtext.widgets import RichTextarea
from formset.widgets import DualSortableSelector


class RichTextField(JSONField):
    def formfield(self, **kwargs):
        form_field = super().formfield(**kwargs)
        if not isinstance(form_field.widget, RichTextarea):
            form_field.widget = RichTextarea()
        return form_field


class SortableMultipleChoiceMixin:
    def clean(self, value):
        qs = super().clean(value)
        return qs, value


class SortableManyToManyField(ManyToManyField):
    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_ordering_enabled(**kwargs),
            *self._check_related_model(**kwargs),
        ]

    def _check_ordering_enabled(self, **kwargs):
        if not self.remote_field.through._meta.ordering:
            return [
                checks.Error(
                    "SortableManyToManyField must point to a mapping model with enabled ordering.",
                    obj=self,
                    id="fields.E341",
                )
            ]
        return []

    def _check_related_model(self, **kwargs):
        try:
            fields = self.remote_field.through._meta.fields
            next(iter(f for f in fields if getattr(f, 'related_model', None) is self.related_model))
        except StopIteration:
            return [
                checks.Error(
                    f"{self.remote_field.through} implementing the many-to-many relation must have a ForeignKey on '{self.related_model}'.",
                    obj=self,
                    id="fields.E342",
                )
            ]
        return []

    def value_from_object(self, obj):
        if obj.pk is None:
            return []
        # find the field in the M2M relation pointing on our related model ('to' in constructor)
        through = self.remote_field.through
        field = next(iter(f for f in through._meta.fields if getattr(f, 'related_model', None) is self.related_model))
        return [getattr(item, field.name) for item in through._default_manager.select_related(field.name)]

    def save_form_data(self, instance, data):
        qs, orig_value = data
        super().save_form_data(instance, qs)
        # after assigning the M2M relation the ordering is updated
        mrm = getattr(instance, self.attname)
        order_field_name = mrm.through._meta.ordering[0]
        for order, target_pk in enumerate(orig_value, 1):
            filter_kwargs = {
                mrm.source_field.attname: instance.pk,
                mrm.target_field.attname: target_pk,
            }
            mrm.through._default_manager.filter(**filter_kwargs).update(**{order_field_name: order})

    def formfield(self, **kwargs):
        form_field = super().formfield(**kwargs)
        form_field.__class__ = type(
            form_field.__class__.__name__,
            (SortableMultipleChoiceMixin, form_field.__class__),
            {}
        )
        if not isinstance(form_field.widget, DualSortableSelector):
            form_field.widget = DualSortableSelector()
        return form_field
