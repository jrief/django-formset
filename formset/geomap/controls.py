from django.template.loader import get_template, select_template
from django.utils.functional import cached_property
from django.utils.translation import gettext, gettext_lazy as _

from formset.dialog import DialogForm


class ControlElement:
    template_name = 'formset/geomap/control.html'
    name = None
    label = None
    dialog_forms = []

    def __init__(self, label=None, dialog_forms=None):
        if isinstance(label, str):
            self.label = label
        if isinstance(dialog_forms, (list, tuple)) and all(isinstance(f, DialogForm) for f in dialog_forms):
            self.dialog_forms.extend(dialog_forms)

    def get_template(self, renderer):
        templates = [
            self.template_name.format(framework=renderer.framework),
            self.template_name.format(framework='default'),
        ]
        return select_template(templates)

    @cached_property
    def button_icon(self):
        if icon := getattr(self, 'icon', None):
            return icon
        return f'formset/icons/{self.name.lower()}.svg'

    def get_context(self):
        return {
            'name': self.name,
            'title': self.label,
            'icon': self.button_icon,
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


class PointEditor(ControlElement):
    name = 'point-editor'
    label = _("Edit Point")
    icon = 'formset/icons/map-pin.svg'
