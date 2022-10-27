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

    def render(self, renderer):
        template = self.get_template(renderer)
        context = {}
        if name := getattr(self, 'name', None):
            context.update(name=name)
        if label := getattr(self, 'label', None):
            context.update(label=label)
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


class Bold(ControlElement):
    name = 'bold'
    label = _("Bold")


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
