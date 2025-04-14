from django.db.models.fields.json import JSONField

from formset.formfields import collection


class CollectionField(JSONField):
    def __init__(self, **kwargs):
        kwargs.setdefault('default', dict)
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', collection.CollectionField)
        return super().formfield(**kwargs)
