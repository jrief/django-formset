import json

from django.contrib.staticfiles.storage import staticfiles_storage
from django.template.loader import get_template, select_template
from django.utils.translation import gettext, gettext_lazy as _

from formset.dialog import DialogForm


class ControlElement:
    template_name = 'formset/geomap/control.html'
    identifier = None
    label = None
    dialog_forms = []
    min_entries = None
    max_entries = None

    def __init__(
        self,
        identifier=None,
        label=None,
        add_button_icon=None,
        delete_button_icon=None,
        marker=None,
        dialog_forms=None,
        min_entries=None,
        max_entries=None,
    ):
        if isinstance(identifier, str):
            self.identifier = identifier
        if isinstance(label, str):
            self.label = label
        if isinstance(add_button_icon, str):
            self.add_button_icon = add_button_icon
        if isinstance(delete_button_icon, str):
            self.delete_button_icon = delete_button_icon
        if isinstance(marker, dict):
            self.marker = marker
        if isinstance(dialog_forms, (list, tuple)) and all(isinstance(f, DialogForm) for f in dialog_forms):
            self.dialog_forms = list(dialog_forms)
        if isinstance(min_entries, int):
            self.min_entries = min_entries
        if isinstance(max_entries, int):
            self.max_entries = max_entries

    def get_template(self, renderer):
        templates = [
            self.template_name.format(framework=renderer.framework),
            self.template_name.format(framework='default'),
        ]
        return select_template(templates)

    def get_context(self):
        name = self.__class__.__name__
        return {
            'name': name,
            'identifier': self.identifier,
            'title': self.label,
            'add_button_icon': getattr(self, 'add_button_icon', f'formset/geomap/icons/add-{name.lower()}.svg'),
            'delete_button_icon': getattr(self, 'delete_button_icon', f'formset/geomap/icons/delete-layer.svg'),
            'marker': json.dumps(getattr(self, 'marker', {})),
            'min_entries': self.min_entries,
            'max_entries': self.max_entries,
        }

    def clean_content(self, richtext_field, content):
        """
        Hook to clean the content returned by the Richtext editor element.
        """

    def render(self, renderer, context=None):
        template = self.get_template(renderer)
        if context is None:
            context = self.get_context()
        return template.render(context)


default_marker = {
    'iconUrl': staticfiles_storage.url('formset/icons/marker-icon.svg'),
    'iconSize': [25, 41],
    'iconAnchor': [13, 41],
    'popupAnchor': [-2, -44],
    'shadowUrl': staticfiles_storage.url('formset/icons/marker-shadow.png'),
    'shadowSize': [68, 68],
    'shadowAnchor': [22, 68],
}


class PointEditor(ControlElement):
    identifier = 'default-marker'
    label = _("Edit Marker Point")
    add_button_icon = 'formset/geomap/icons/add-marker.svg'
    delete_button_icon = 'formset/geomap/icons/delete-marker.svg'
    marker = default_marker

    def __init__(self, min_markers=None, max_markers=None, **kwargs):
        super().__init__(min_entries=min_markers, max_entries=max_markers, **kwargs)


class PolylineEditor(ControlElement):
    identifier = 'polyline'
    label = _("Edit Polyline")
    add_button_icon = 'formset/geomap/icons/add-polyline.svg'
    delete_button_icon = 'formset/geomap/icons/delete-polyline.svg'

    def __init__(self, min_polylines=None, max_polylines=None, **kwargs):
        super().__init__(min_entries=min_polylines, max_entries=max_polylines, **kwargs)


class PolygonEditor(ControlElement):
    identifier = 'polygon'
    label = _("Edit Polygon")
    add_button_icon = 'formset/geomap/icons/add-polygon.svg'
    delete_button_icon = 'formset/geomap/icons/delete-polygon.svg'

    def __init__(self, min_polygons=None, max_polygons=None, **kwargs):
        super().__init__(min_entries=min_polygons, max_entries=max_polygons, **kwargs)


class MultiPolygonEditor(ControlElement):
    identifier = 'multipolygon'
    label = _("Edit Multi-Polygon")
    add_button_icon = 'formset/geomap/icons/add-multipolygon.svg'
    delete_button_icon = 'formset/geomap/icons/delete-multipolygon.svg'
    extend_button_icon = 'formset/geomap/icons/extend-multipolygon.svg'

    def __init__(
        self,
        extend_button_icon=None,
        **kwargs,
    ):
        if extend_button_icon is not None:
            self.extend_button_icon = extend_button_icon
        super().__init__(**kwargs)
