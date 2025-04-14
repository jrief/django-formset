from django.forms.widgets import Widget
from django.template.loader import get_template
from django.utils.functional import cached_property


class Button(Widget):
    template_name = 'formset/default/widgets/button.html'
    button_type = 'button'
    action = None
    button_variant = None
    icon_path = None
    icon_left = None

    def __init__(
        self,
        attrs=None,
        action=None,
        button_variant=None,
        auto_disable=False,
        icon_path=None,
        icon_left=False
    ):
        if action is not None:
            self.action = action
        if button_variant:
            self.button_variant = button_variant
        self.auto_disable = auto_disable
        if icon_path:
            self.icon_path = icon_path
        self.icon_left = icon_left
        super().__init__(attrs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if self.action is not None:
            attrs['df-click'] = self.action
        if self.auto_disable:
            attrs['auto-disable'] = True
        return attrs

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['label'] = context['widget']['attrs'].pop('label', None)  # for buttons, the label is the value
        context['widget']['type'] = self.button_type
        context['widget']['variant'] = self.button_variant
        context['icon_element'] = self.icon_element
        context['icon_left'] = self.icon_left
        return context

    @cached_property
    def icon_element(self):
        if self.icon_path:
            template = get_template(self.icon_path)
            return template.render()
        return ''
