from django.utils.html import format_html

from formset.mixins import default


class WidgetMixin(default.WidgetMixin):
    template_mapping = {
        'RadioSelect': 'formset/bootstrap/widgets/radio.html',
        'CheckboxInput': 'formset/bootstrap/widgets/checkbox.html',
        'CheckboxSelectMultiple': 'formset/bootstrap/widgets/checkboxselectmultiple.html',
    }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if self.__class__.__name__ == 'CheckboxInput':
            context['checkbox_label'] = attrs.pop('checkbox_label')
        return context


class FormMixin(default.FormMixin):
    field_css_classes = 'form-group'
    help_text_html='<span class="form-text text-muted">%s</span>'
    widget_mixin = WidgetMixin
    widget_css_classes = {
        'text': 'form-control',
        'email': 'form-control',
        'date': 'form-control',
        'checkbox': 'form-check-input',
        'checkboxselectmultiple': 'form-check-input',
        'radioselect': 'form-check-input',
        'select': 'form-control',
        'selectmultiple': 'form-control',
        'number': 'form-control',
        'textarea': 'form-control',
        'password': 'form-control',
    }

    def render_label(self, bound_field, contents, attrs, label_suffix):
        label_css_classes = getattr(self, 'label_css_classes', None)
        if bound_field.widget_type == 'checkbox':
            if label_css_classes:
                label_tag = format_html('<div class="{}"></div>', label_css_classes)
            else:
                label_tag = ''
        else:
            if label_css_classes:
                attrs = dict(attrs or {})
                if 'class' in attrs:
                    attrs['class'] += ' ' + label_css_classes
                else:
                    attrs['class'] = label_css_classes
            label_tag = super().render_label(bound_field, contents, attrs, label_suffix)
        return label_tag

    def get_widget_attrs(self, bound_field, attrs, widget):
        attrs = super().get_widget_attrs(bound_field, attrs, widget)

        # checkbox widgets render their label themselves
        if bound_field.widget_type == 'checkbox':
            attrs['checkbox_label'] = bound_field.label

        return attrs
