from django.forms.widgets import Textarea
from django.utils.html import format_html, format_html_join

from formset.richtext import controls


class RichTextarea(Textarea):
    template_name = 'formset/default/widgets/richtextarea.html'
    control_elements = [
        controls.Heading(),
        controls.Bold(),
        controls.Italic(),
        controls.Link(),
        controls.BulletList(),
        controls.HorizontalRule(),
        controls.Separator(),
        controls.ClearFormat(),
        controls.Undo(),
        controls.Redo(),
    ]

    def __init__(self, attrs=None, control_elements=None):
        super().__init__(attrs)
        if control_elements is not None:
            self.control_elements = control_elements

    def format_value(self, value):
        return value or ''

    def value_from_datadict(self, data, files, name):
        # TODO[link]: convert internal links to reverse lookups
        # TODO[img]: extract images and move them to the upload area
        return data.get(name, {})

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['use_json'] = attrs.get('use_json', False)
        context['widget']['attrs'].pop('use_json', None)
        return context

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        control_panel = format_html_join('', '{0}', ((elm.render(renderer),) for elm in self.control_elements))
        modal_dialogs = format_html_join('\n', '{0}', (
            (format_html('<dialog richtext-opener="{0}">{1}</dialog>', elm.name, elm.dialog_class(renderer=renderer)),)
            for elm in self.control_elements if getattr(elm, 'dialog_class', None))
        )
        context.update(
            control_panel=control_panel,
            modal_dialogs=modal_dialogs,
        )
        return self._render(self.template_name, context, renderer)
