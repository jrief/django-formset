from formset.mixins import default


class WidgetMixin(default.WidgetMixin):
    template_mapping = {
        'RadioSelect': 'formset/foundation/widgets/radio.html',
        'CheckboxInput': 'formset/foundation/widgets/checkbox.html',
        'CheckboxSelectMultiple': 'formset/foundation/widgets/checkboxselectmultiple.html',
    }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if context.get('inlined_checks') is True:
            for group, options, _ in context['widget']['optgroups']:
                options[0]['template_name'] = 'formset/foundation/widgets/inlined_checks.html'
        return context


class FormMixin(default.FormMixin):
    help_text_html='<p class="help-text">%s</p>'
    widget_mixin = WidgetMixin

    def render_label(self, bound_field, contents, attrs, label_suffix):
        if bound_field.widget_type == 'checkbox':
            # label is rendered by formset/foundation/widgets/checkbox.html
            label_tag = ''
        else:
            label_tag = super().render_label(bound_field, contents, attrs, label_suffix)
        return label_tag

    def get_widget_attrs(self, bound_field, attrs, widget):
        attrs = super().get_widget_attrs(bound_field, attrs, widget)

        # checkbox widgets render their label themselves
        if bound_field.widget_type == 'checkbox':
            attrs['checkbox_label'] = bound_field.label

        return attrs
