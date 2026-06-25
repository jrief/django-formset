from django.forms.fields import JSONField

from formset.widgets.geomap import GeoMapWidget


class GeoMapField(JSONField):
    widget = GeoMapWidget

    def clean(self, value):
        cleaned_data = super().clean(value)
        return cleaned_data
