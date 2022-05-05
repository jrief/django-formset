from django.core import checks
from django.db.models.fields.related import ManyToManyField


class SortableMultipleChoiceMixin:
    def clean(self, value):
        qs = super().clean(value)
        return qs, value


class SortableManyToManyField(ManyToManyField):
    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_ordering_enabled(**kwargs),
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
            mrm.through.objects.filter(**filter_kwargs).update(**{order_field_name: order})

    def formfield(self, **kwargs):
        form_field = super().formfield(**kwargs)
        class_name = form_field.__class__.__name__
        form_field.__class__ = type(class_name, (SortableMultipleChoiceMixin, form_field.__class__), {})
        return form_field
