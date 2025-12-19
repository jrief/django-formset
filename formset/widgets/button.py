from django.forms.widgets import Widget
from django.template.loader import get_template, render_to_string
from django.utils.functional import cached_property


class Button(Widget):
    template_name = 'formset/default/widgets/button.html'
    button_type = 'button'
    action = None
    button_variant = None
    button_size = None
    icon_path = None
    icon_char = None
    icon_left = None

    def __init__(
        self,
        attrs=None,
        action=None,
        button_variant=None,
        button_size=None,
        auto_disable=False,
        omit_restore=False,
        icon_path=None,
        icon_char=None,
        icon_left=False,
    ):
        if action is not None:
            self.action = action
        if button_variant:
            self.button_variant = button_variant
        if button_size:
            self.button_size = button_size
        self.auto_disable = auto_disable
        self.omit_restore = omit_restore
        if icon_path and icon_char:
            raise ValueError("Specify either icon_path or icon_char, not both.")
        if icon_path:
            self.icon_path = icon_path
        if icon_char:
            self.icon_char = icon_char
        self.icon_left = icon_left
        super().__init__(attrs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if self.action is not None:
            attrs['df-click'] = self.action
        if self.auto_disable:
            attrs['auto-disable'] = True
        if self.omit_restore:
            attrs['omit-restore'] = True
        return attrs

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['label'] = context['widget']['attrs'].pop('label', None)  # for buttons, the label is the value
        context['widget']['type'] = self.button_type
        context['widget']['variant'] = self.button_variant
        context['widget']['size'] = self.button_size
        context['icon_element'] = self.icon_element
        context['icon_left'] = self.icon_left
        return context

    @cached_property
    def icon_element(self):
        if self.icon_char:
            icon = self.icon_char
        elif self.icon_path:
            icon = render_to_string(self.icon_path)
        else:
            return ''
        return icon
