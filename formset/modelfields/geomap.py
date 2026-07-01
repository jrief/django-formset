from django.db.models.fields.json import JSONField

from formset.formfields import geomap


class GeoMapField(JSONField):
    def formfield(self, **kwargs):
        kwargs.setdefault('form_class', geomap.GeoMapField)
        return super().formfield(**kwargs)
