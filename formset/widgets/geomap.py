from django.forms.widgets import Textarea


class GeoMapWidget(Textarea):
    """
    Widget to be used by :class:`formset.formfields.geomap.GeoMapField`.
    """

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['is'] = 'django-geo-map'
        return attrs
