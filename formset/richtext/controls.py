import re

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import select_template
from django.utils.translation import gettext_lazy as _

from formset.richtext.dialogs import ImageFormDialog, LinkFormDialog


class ControlElement:
    template_name = 'formset/{framework}/buttons/richtext_control.html'

    def get_template(self, renderer):
        templates = [
            self.template_name.format(framework=renderer.framework),
            self.template_name.format(framework='default'),
        ]
        return select_template(templates)

    def render(self, renderer, context=None):
        template = self.get_template(renderer)
        if context is None:
            context = {}
        if label := getattr(self, 'label', None):
            context.update(label=label)
        if name := getattr(self, 'name', None):
            context.update(name=name)
        if icon := getattr(self, 'icon', None):
            context.update(icon=icon)
        elif name:
            context.update(icon=f'formset/icons/{name.lower()}.svg')
        else:
            context.update(icon=f'formset/icons/questionmark.svg')
        return template.render(context)


class Heading(ControlElement):
    name = 'heading'
    label = _("Heading")
    levels = [1, 2, 3, 4, 5, 6]
    template_name = 'formset/{framework}/buttons/richtext_heading.html'

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
    name = 'textAlign'
    label = _("Text Align")
    alignments = ['left', 'center', 'right', 'justify']
    template_name = 'formset/{framework}/buttons/richtext_align.html'

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
    name = 'textColor'
    label = _("Text Color")
    template_name = 'formset/{framework}/buttons/richtext_color.html'
    colors = [None]

    def __init__(self, colors):
        if not isinstance(colors, (list, tuple)) or len(colors) == 0:
            raise ImproperlyConfigured("TextColor() requires a list with at least one color")
        pattern = re.compile(r'^rgb\(\d{1,3}, \d{1,3}, \d{1,3}\)$')
        for color in colors:
            if not re.match(pattern, color):
                raise ImproperlyConfigured(f"Given color {color} is not in format rgb(r, g, b)")
        self.colors.extend(colors)

    def render(self, renderer):
        template = self.get_template(renderer)
        return template.render({
            'colors': self.colors,
        })


class TextIndent(ControlElement):
    def __init__(self, indent='indent'):
        if indent == 'indent':
            self.name = 'textIndent:indent'
            self.label = _("Indent First Line")
            self.icon = 'formset/icons/indentfirstline.svg'
        elif indent == 'outdent':
            self.name = 'textIndent:outdent'
            self.label = _("Outdent First Line")
            self.icon = 'formset/icons/outdentfirstline.svg'
        else:
            raise ImproperlyConfigured("Misconfigured argument: indent")


class TextMargin(ControlElement):
    def __init__(self, indent):
        if indent == 'increase':
            self.name = 'textMargin:increase'
            self.label = _("Increase Margin")
            self.icon = 'formset/icons/increasemargin.svg'
        elif indent == 'decrease':
            self.name = 'textMargin:decrease'
            self.label = _("Decrease Margin")
            self.icon = 'formset/icons/decreasemargin.svg'
        else:
            raise ImproperlyConfigured("Misconfigured argument: indent")


class Bold(ControlElement):
    name = 'bold'
    label = _("Bold")


class Blockquote(ControlElement):
    name = 'blockquote'
    label = _("Blockquote")


class CodeBlock(ControlElement):
    name = 'codeBlock'
    label = _("Code Block")


class HardBreak(ControlElement):
    name = 'hardBreak'
    label = _("Hard Break")


class Italic(ControlElement):
    name = 'italic'
    label = _("Italic")


class Underline(ControlElement):
    name = 'underline'
    label = _("Underline")


class BulletList(ControlElement):
    name = 'bulletList'
    label = _("Bullet List")


class OrderedList(ControlElement):
    name = 'orderedList'
    label = _("Ordered List")


class HorizontalRule(ControlElement):
    name = 'horizontalRule'
    label = _("Horizontal Rule")


class ClearFormat(ControlElement):
    name = 'clearFormat'
    label = _("Clear Format")


class Undo(ControlElement):
    name = 'undo'
    label = _("Undo")


class Redo(ControlElement):
    name = 'redo'
    label = _("Redo")


class Link(ControlElement):
    name = 'link'
    label = _("Link")
    dialog_class = LinkFormDialog


class Image(ControlElement):
    name = 'image'
    label = _("Image")
    dialog_class = ImageFormDialog


class Separator(ControlElement):
    label = _("Separator")
    template_name = 'formset/{framework}/buttons/richtext_separator.html'
