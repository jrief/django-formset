import json

from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import Textarea
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from formset.geomap.controls import ControlElement
from formset.geomap.dialogs import GeoMapDialogForm


class GeoMapWidget(Textarea):
    """
    Widget to be used by :class:`formset.formfields.geomap.GeoMapField`.
    """

    template_name = 'formset/default/widgets/geomap.html'
    controls = None

    def __init__(
        self,
        attrs=None,
        controls_topleft=None,
        controls_topright=None,
        controls_bottomright=None,
        controls_bottomleft=None,
    ):
        super().__init__(attrs)
        if self.controls is None:
            self.controls = {}
        self.controls.setdefault('topleft', [])
        self.controls.setdefault('topright', [])
        self.controls.setdefault('bottomright', [])
        self.controls.setdefault('bottomleft', [])
        if isinstance(controls_topleft, list):
            self.controls['topleft'] = list(controls_topleft)
        if isinstance(controls_topright, list):
            self.controls['topright'] = list(controls_topright)
        if isinstance(controls_bottomright, list):
            self.controls['bottomright'] = list(controls_bottomright)
        if isinstance(controls_bottomleft, list):
            self.controls['bottomleft'] = list(controls_bottomleft)
        self.check_settings()

    def check_settings(self):
        """
        Validate the widget's configuration.
        """
        editor_identifiers, dialog_form_extensions = set(), set()
        for position in ['topleft', 'topright', 'bottomright', 'bottomleft']:
            if position not in self.controls:
                continue
            for editor in self.controls[position]:
                if isinstance(editor, ControlElement):
                    if editor.identifier in editor_identifiers:
                        raise ImproperlyConfigured(
                            f"The editor identifier “{editor.identifier}” has already been registered on {self}."
                        )
                    editor_identifiers.add(editor.identifier)
                    for dialog_form in editor.dialog_forms:
                        if dialog_form.extension in dialog_form_extensions:
                            raise ImproperlyConfigured(
                                f"The dialog form using extension “{dialog_form.extension}” has "
                                f"already been registered on {self}."
                            )
                        dialog_form_extensions.add(dialog_form.extension)
                elif isinstance(editor, (list, tuple)):
                    for sub_editor in editor:
                        if sub_editor.identifier in editor_identifiers:
                            raise ImproperlyConfigured(
                                f"The editor identifier “{sub_editor.identifier}” has already been registered on {self}."
                            )
                        editor_identifiers.add(sub_editor.identifier)
                        for dialog_form in sub_editor.dialog_forms:
                            if dialog_form.extension in dialog_form_extensions:
                                raise ImproperlyConfigured(
                                    f"The dialog form using extension “{dialog_form.extension}” has "
                                    f"already been registered on {self}."
                                )
                            dialog_form_extensions.add(dialog_form.extension)


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
        def render_controls(controls):
            return

        def render_dialog(dialog_form, described_by):
            dialog_form.prefix = f'{form_prefix}.{name}' if form_prefix else name
            dialog_context = {**dialog_form.get_context(), 'described_by': described_by}
            return dialog_form.render(context=dialog_context, renderer=renderer)

        form_prefix = attrs.pop('form_prefix', None)  # added by BoundField.build_widget_attrs
        context = self.get_context(name, value, attrs)
        control_elements, popups, dialog_forms = [], [], []
        for position, controls in self.controls.items():
            rendered_controls = [[]]
            for control_element in controls:
                if isinstance(control_element, ControlElement):
                    rendered_controls[-1].append(control_element.render(renderer))
                    popups.append({
                        'labeled_by': control_element.identifier,
                        'dialogs': [],
                        'delete_button_icon': control_element.delete_button_icon,
                        'extend_button_icon': getattr(control_element, 'extend_button_icon', None),
                    })
                    for dialog_form in control_element.dialog_forms:
                        if isinstance(dialog_form, GeoMapDialogForm):
                            dialog_forms.append(render_dialog(dialog_form, control_element.identifier))
                            popups[-1]['dialogs'].append({
                                'prefix': dialog_form.prefix,
                                'icon': dialog_form.button_icon,
                                'title': dialog_form.title,
                            })
                elif isinstance(control_element, (list, tuple)):
                    rendered_controls.append([ctrl_elm.render(renderer) for ctrl_elm in control_element])
                    rendered_controls.append([])
                    for ctrl_elm in control_element:
                        popups.append({
                            'labeled_by': ctrl_elm.identifier,
                            'dialogs': [],
                            'delete_button_icon': ctrl_elm.delete_button_icon,
                            'extend_button_icon': getattr(ctrl_elm, 'extend_button_icon', None),
                        })
                        for dialog_form in ctrl_elm.dialog_forms:
                            if isinstance(dialog_form, GeoMapDialogForm):
                                dialog_forms.append(render_dialog(dialog_form, ctrl_elm.identifier))
                                popups[-1]['dialogs'].append({
                                    'prefix': dialog_form.prefix,
                                    'icon': dialog_form.button_icon,
                                    'title': dialog_form.title,
                                })
            control_elements.append(
                format_html(
                    '<div aria-current="{position}">{controls}</div>',
                    position=position,
                    controls=format_html_join(
                        '',
                        '<div class="leaflet-bar">{0}</div>',
                        ((mark_safe(''.join(rc)),) for rc in rendered_controls if rc),
                    ),
                )
            )
        context.update(
            control_elements=control_elements,
            popups=popups,
            dialog_forms=dialog_forms,
        )
        return self._render(self.template_name, context, renderer)
