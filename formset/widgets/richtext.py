import json

from django.core.exceptions import ValidationError
from django.core.validators import EMPTY_VALUES
from django.forms.widgets import Textarea
from django.utils.html import format_html_join, strip_tags
from django.utils.translation import gettext

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
        value = data.get(name)
        if use_json := self.attrs.get('use_json'):
            if value in EMPTY_VALUES:
                value = {'type': 'doc', 'content': []}
            if not isinstance(value, dict):
                raise ValidationError(gettext("The submitted data is not a valid JSON structure."))
        else:
            if not isinstance(value, str):
                raise ValidationError(gettext("The submitted data is not a valid text string."))
        if max_length := self.attrs.get('maxlength'):
            if use_json:
                text_length = self._compute_text_length(value.get('content', []))
            else:
                text_length = len(strip_tags(value))
            if text_length > int(max_length):
                msg = gettext("The submitted text is too long ({text_length} characters, max. {max_length})")
                raise ValidationError(msg.format(text_length=text_length, max_length=max_length))
        return value

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
        def add_dialog(dialog_form):
            dialog_form.prefix = f'{form_prefix}.{name}' if form_prefix else name
            dialog_context = dialog_form.get_context()
            dialog_forms.append(dialog_form.render(context=dialog_context, renderer=renderer))

        form_prefix = attrs.pop('form_prefix', None)  # added by BoundField.build_widget_attrs
        context = self.get_context(name, value, attrs)
        control_panel = format_html_join('', '{0}', (
            [elm.render(renderer)] for elm in self.control_elements
        ))
        dialog_forms = []
        for control_element in self.control_elements:
            if isinstance(control_element, controls.DialogControl):
                add_dialog(control_element.dialog_form)
            elif isinstance(control_element, controls.Group):
                for elm in control_element:
                    if isinstance(elm, controls.DialogControl):
                        add_dialog(elm.dialog_form)

        context.update(
            control_panel=control_panel,
            dialog_forms=dialog_forms,
        )
        return self._render(self.template_name, context, renderer)

    @classmethod
    def _compute_text_length(cls, contents):
        accumulated_length = 0
        for content in contents:
            if content.get('type') == 'text':
                accumulated_length += len(content.get('text', ''))
            else:
                child_contents = content.get('content')
                if isinstance(child_contents, list):
                    accumulated_length += cls._compute_text_length(child_contents)
        return accumulated_length
