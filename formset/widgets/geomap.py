import json

from django.forms.widgets import Textarea
from django.utils.html import format_html, format_html_join

from formset.geomap.dialogs import GeoMapDialogForm


class GeoMapWidget(Textarea):
    """
    Widget to be used by :class:`formset.formfields.geomap.GeoMapField`.
    """

    template_name = 'formset/default/widgets/geomap.html'
    controls = {'topleft': [], 'topright': [], 'bottomright': [], 'bottomleft': []}

    def __init__(
        self,
        attrs=None,
        controls_topleft=None,
        controls_topright=None,
        controls_bottomright=None,
        controls_bottomleft=None,
    ):
        super().__init__(attrs)
        if isinstance(controls_topleft, list):
            self.controls['topleft'] = controls_topleft
        if isinstance(controls_topright, list):
            self.controls['topright'] = controls_topright
        if isinstance(controls_bottomright, list):
            self.controls['bottomright'] = controls_bottomright
        if isinstance(controls_bottomleft, list):
            self.controls['bottomleft'] = controls_bottomleft

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['is'] = 'django-geo-map'
        return attrs

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if isinstance(value, dict):
            context['widget']['attrs']['data-content'] = json.dumps(value)
        elif isinstance(value, str) and '"type": "FeatureCollection"' in value:  # already JSONified
            context['widget']['attrs']['data-content'] = value
        context['widget'].pop('value', None)  # we don't want the <textarea> to contain any JSON data
        return context

    def render(self, name, value, attrs=None, renderer=None):
        def render_dialog(dialog_form):
            dialog_form.prefix = f'{form_prefix}.{name}' if form_prefix else name
            dialog_context = dialog_form.get_context()
            return dialog_form.render(context=dialog_context, renderer=renderer)

        form_prefix = attrs.pop('form_prefix', None)  # added by BoundField.build_widget_attrs
        context = self.get_context(name, value, attrs)
        control_elements, popups, dialog_forms = [], [], []
        for position, controls in self.controls.items():
            control_elements.append(
                format_html(
                    '<div aria-current="{position}" class="leaflet-bar">{controls}</div>',
                    position=position,
                    controls=format_html_join('', '{0}', ([elm.render(renderer)] for elm in controls)),
                )
            )
            for control_element in controls:
                popups.append({'labeled_by': control_element.extension, 'dialogs': []})
                for dialog_form in control_element.dialog_forms:
                    if isinstance(dialog_form, GeoMapDialogForm):
                        dialog_forms.append(render_dialog(dialog_form))
                        popups[-1]['dialogs'].append({'prefix': dialog_form.prefix, 'icon': dialog_form.button_icon})

        context.update(
            control_elements=control_elements,
            popups=popups,
            dialog_forms=dialog_forms,
        )
        return self._render(self.template_name, context, renderer)
