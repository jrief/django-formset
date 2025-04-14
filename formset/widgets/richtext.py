import json

from django.forms.widgets import Textarea
from django.utils.html import format_html_join

from formset.richtext import controls


class RichTextarea(Textarea):
    template_name = 'formset/default/widgets/richtextarea.html'
    control_elements = [
        controls.Heading(),
        controls.Bold(),
        controls.Italic(),
        controls.BulletList(),
        controls.HorizontalRule(),
        controls.Separator(),
        controls.ClearFormat(),
        controls.Undo(),
        controls.Redo(),
    ]

    def __init__(self, attrs=None, control_elements=None):
        super().__init__(attrs)
        if isinstance(control_elements, list):
            self.control_elements = control_elements

    def format_value(self, value):
        return value or ''

    def value_from_datadict(self, data, files, name):
        # TODO[link]: convert internal links to reverse lookups
        # TODO[img]: extract images and move them to the upload area
        return data.get(name, {})

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if attrs.get('use_json') or self.attrs.get('use_json'):
            context['use_json'] = True
            if isinstance(value, dict):
                context['widget']['attrs']['data-content'] = json.dumps(value)
            elif isinstance(value, str) and '"type": "doc"' in value:  # already JSONified
                context['widget']['attrs']['data-content'] = value
            else:
                context['widget']['attrs']['data-content'] = '{"type": "doc"}'  # empty document
            context['widget'].pop('value', None)
        context['widget']['attrs'].pop('use_json', None)
        return context

    def render(self, name, value, attrs=None, renderer=None):
        def add_dialog(control_element):
            dialog_form = control_element.dialog_form
            dialog_context = dialog_form.get_context()
            dialog_form.induce_open = f'dialog_{dialog_form.extension}:active'
            dialog_form.auto_id = '{form}_{control}_%s'.format(**attrs, control=dialog_form.extension)
            dialog_forms.append(dialog_form.render(context=dialog_context, renderer=renderer))

        context = self.get_context(name, value, attrs)
        control_panel = format_html_join('', '{0}', (
            [elm.render(renderer)] for elm in self.control_elements
        ))
        dialog_forms = []
        for control_element in self.control_elements:
            if isinstance(control_element, controls.DialogControl):
                add_dialog(control_element)
            elif isinstance(control_element, controls.Group):
                for elm in control_element:
                    if isinstance(elm, controls.DialogControl):
                        add_dialog(elm)

        context.update(
            control_panel=control_panel,
            dialog_forms=dialog_forms,
        )
        return self._render(self.template_name, context, renderer)
