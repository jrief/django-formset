import re

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import select_template
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from formset.dialog import DialogForm


class ControlElement:
    extension = None
    template_name = 'formset/richtext/control.html'

    def get_template(self, renderer):
        templates = [
            self.template_name.format(framework=renderer.framework),
            self.template_name.format(framework='default'),
        ]
        return select_template(templates)

    @cached_property
    def button_icon(self):
        if not (icon := getattr(self, 'icon', None)):
            icon = f'formset/icons/{self.extension.lower()}.svg'
        return icon

    def get_context(self):
        return {
            'extension': self.extension,
            'label': self.label,
            'icon': self.button_icon,
        }

    def render(self, renderer, context=None):
        template = self.get_template(renderer)
        if context is None:
            context = self.get_context()
        return template.render(context)


class Heading(ControlElement):
    extension = 'heading'
    label = _("Heading")
    levels = [1, 2, 3, 4, 5, 6]
    template_name = 'formset/richtext/heading.html'

    def __init__(self, levels=None):
        if isinstance(levels, (list, tuple)):
            self.levels = levels
        elif isinstance(levels, (str, int)):
            self.levels = [levels]
        self.levels = [str(l) for l in self.levels]

    def render(self, renderer):
        template = self.get_template(renderer)
        return template.render({'levels': self.levels})


class TextAlign(ControlElement):
    extension = 'textAlign'
    label = _("Text Align")
    alignments = ['left', 'center', 'right', 'justify']
    template_name = 'formset/richtext/align.html'

    def __init__(self, alignments=None, default_alignment=None):
        if isinstance(alignments, str):
            alignments = [alignments]
        elif not isinstance(alignments, (list, tuple)):
            alignments = self.alignments
        elif len(alignments) == 0:
            raise ImproperlyConfigured(
                f"At least one alignment must be given for {self.__class__.__name__}"
            )
        for a in alignments:
            if a not in self.alignments:
                raise ImproperlyConfigured(
                    f"'{a}' in not a valid alignment for {self.__class__.__name__}"
                )
        self.alignments = alignments

        if default_alignment is None:
            self.default_alignment = self.alignments[0]
        elif default_alignment not in self.alignments:
            raise ImproperlyConfigured(
                f"'{default_alignment}' in not a valid default alignment for {self.__class__.__name__}"
            )
        else:
            self.default_alignment = default_alignment

    def render(self, renderer):
        template = self.get_template(renderer)
        return template.render({
            'alignments': self.alignments,
            'default_alignment': self.default_alignment,
        })


class TextColor(ControlElement):
    extension = 'textColor'
    label = _("Text Color")
    template_name = 'formset/richtext/color.html'
    class_based = None

    def __init__(self, colors):
        if not isinstance(colors, (list, tuple)) or len(colors) == 0:
            raise ImproperlyConfigured("TextColor() requires a list with at least one color")
        rgb_pattern = re.compile(r'^rgb\(\d{1,3}, \d{1,3}, \d{1,3}\)$')
        class_pattern = re.compile(r'^-?[_a-zA-Z]+[_a-zA-Z0-9-]*$')
        for color in colors:
            if re.match(rgb_pattern, color):
                if self.class_based is True:
                    raise ImproperlyConfigured(f"Given color {color} is not in format rgb(r, g, b)")
                self.class_based = False
            elif re.match(class_pattern, color):
                if self.class_based is False:
                    raise ImproperlyConfigured(f"Given color {color} does not look like a valid CSS class name")
                self.class_based = True
        self.colors = [None]  # the default color
        self.colors.extend(colors)

    def render(self, renderer):
        template = self.get_template(renderer)
        return template.render({
            'colors': self.colors,
            'class_based': self.class_based,
        })


class TextIndent(ControlElement):
    def __init__(self, indent='indent'):
        if indent == 'indent':
            self.extension = 'textIndent:indent'
            self.label = _("Indent First Line")
            self.icon = 'formset/icons/indentfirstline.svg'
        elif indent == 'outdent':
            self.extension = 'textIndent:outdent'
            self.label = _("Outdent First Line")
            self.icon = 'formset/icons/outdentfirstline.svg'
        else:
            raise ImproperlyConfigured("Misconfigured argument: indent")


class TextMargin(ControlElement):
    def __init__(self, indent):
        if indent == 'increase':
            self.extension = 'textMargin:increase'
            self.label = _("Increase Margin")
            self.icon = 'formset/icons/increasemargin.svg'
        elif indent == 'decrease':
            self.extension = 'textMargin:decrease'
            self.label = _("Decrease Margin")
            self.icon = 'formset/icons/decreasemargin.svg'
        else:
            raise ImproperlyConfigured("Misconfigured argument: indent")


class Bold(ControlElement):
    extension = 'bold'
    label = _("Bold")


class Blockquote(ControlElement):
    extension = 'blockquote'
    label = _("Blockquote")


class CodeBlock(ControlElement):
    extension = 'codeBlock'
    label = _("Code Block")


class HardBreak(ControlElement):
    extension = 'hardBreak'
    label = _("Hard Break")


class Italic(ControlElement):
    extension = 'italic'
    label = _("Italic")


class Underline(ControlElement):
    extension = 'underline'
    label = _("Underline")


class BulletList(ControlElement):
    extension = 'bulletList'
    label = _("Bullet List")


class OrderedList(ControlElement):
    extension = 'orderedList'
    label = _("Ordered List")


class HorizontalRule(ControlElement):
    extension = 'horizontalRule'
    label = _("Horizontal Rule")


class ClearFormat(ControlElement):
    extension = 'clearFormat'
    label = _("Clear Format")


class Strike(ControlElement):
    extension = 'strike'
    label = _("Strike")


class Subscript(ControlElement):
    extension = 'subscript'
    label = _("Subscript")


class Superscript(ControlElement):
    extension = 'superscript'
    label = _("Superscript")


class Undo(ControlElement):
    extension = 'undo'
    label = _("Undo")


class Redo(ControlElement):
    extension = 'redo'
    label = _("Redo")


class DialogControl(ControlElement):
    template_name = 'formset/richtext/dialog_control.html'

    def __init__(self, dialog_form, icon=None):
        if not isinstance(dialog_form, DialogForm):
            raise ImproperlyConfigured("DialogControl() requires a DialogForm instance")
        self.dialog_form = dialog_form
        if icon:
            self.icon = icon

    @cached_property
    def button_icon(self):
        if not (icon := getattr(self, 'icon', None)) and not (icon := getattr(self.dialog_form, 'icon', None)):
            icon = 'formset/icons/activator.svg'
        return icon

    def get_context(self):
        return {
            'extension': self.dialog_form.extension,
            'label': self.dialog_form.title,
            'icon': self.button_icon,
        }


class Separator(ControlElement):
    label = _("Separator")
    template_name = 'formset/richtext/separator.html'

    def render(self, renderer, context=None):
        return super().render(renderer, {})
