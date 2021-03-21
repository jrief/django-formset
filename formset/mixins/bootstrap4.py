import copy

from formset.mixins.default import FormMixin, WidgetMixin


class BootstrapWidgetMixin(WidgetMixin):
    template_mapping = {
        'RadioSelect': 'formset/widgets/bootstrap4/radio.html',
        'CheckboxInput': 'formset/widgets/bootstrap4/checkbox.html',
        'CheckboxSelectMultiple': 'formset/widgets/bootstrap4/checkboxselectmultiple.html',
    }


class BootstrapFormMixin(FormMixin):
    field_css_classes = 'form-group'
    help_text_html='<span class="form-text text-muted">%s</span>'
    widget_css_classes = {
        'text': 'form-control',
        'email': 'form-control',
        'date': 'form-control',
        'select': 'form-control',
        'selectmultiple': 'form-control',
        'number': 'form-control',
        'textarea': 'form-control',
        'password': 'form-control',
    }

    def get_widget(self, field):
        widget = copy.deepcopy(field.widget)
        widget.__class__ = type(widget.__class__.__name__, (BootstrapWidgetMixin, widget.__class__), {})
        return widget
