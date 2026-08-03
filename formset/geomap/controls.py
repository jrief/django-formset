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

    def __init__(self, identifier=None, label=None, button_icon=None, marker=None, dialog_forms=None):
        if isinstance(identifier, str):
            self.identifier = identifier
        if isinstance(label, str):
            self.label = label
        if isinstance(button_icon, str):
            self.button_icon = button_icon
        if isinstance(marker, dict):
            self.marker = marker
        if isinstance(dialog_forms, (list, tuple)) and all(isinstance(f, DialogForm) for f in dialog_forms):
            self.dialog_forms = list(dialog_forms)

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
            'button_icon': getattr(self, 'button_icon', f'formset/icons/{name.lower()}.svg'),
            'marker': json.dumps(getattr(self, 'marker', {})),
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


class Group(list):
    template_name = 'formset/geomap/control_group.html'

    def render(self, renderer, context=None):
        if context is None:
            context = {
                'elements': [element.render(renderer) for element in self],
            }
        template = get_template(self.template_name)
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
    button_icon = 'formset/icons/map-pin.svg'
    marker = default_marker


class PolylineEditor(ControlElement):
    identifier = 'polyline'
    label = _("Edit Polyline")
    button_icon = 'formset/icons/map-polyline.svg'
