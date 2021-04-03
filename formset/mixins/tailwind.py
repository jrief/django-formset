from formset.mixins import default


class WidgetMixin(default.WidgetMixin):
    template_mapping = {
        'RadioSelect': 'formset/tailwind/widgets/radio.html',
        'CheckboxInput': 'formset/tailwind/widgets/checkbox.html',
        'CheckboxSelectMultiple': 'formset/tailwind/widgets/checkboxselectmultiple.html',
    }


class FormMixin(default.FormMixin):
    """
    Class to mix into a Django ``Form`` or ``ModelForm`` class.

    Adopt styles by editing assets/tailwind-styles.css and recompile using:
    ``npm run tailwindcss``
    """
    field_css_classes = 'mb-5'
    help_text_html='<p class="formset-help-text">%s</p>'
    widget_mixin = WidgetMixin
    widget_css_classes = {
        'text': 'formset-text-input',
        'email': 'formset-email-input',
        'date': 'formset-date-input',
        'checkbox': 'formset-checkbox',
        'checkboxselectmultiple': 'formset-checkbox-multiple',
        'radioselect': 'formset-radio-select',
        'select': 'formset-select',
        'selectmultiple': 'formset-select-multiple',
        'number': 'formset-number-input',
        'textarea': 'formset-textarea',
        'password': 'formset-password-input',
    }

    def get_widget_attrs(self, bound_field, attrs, widget):
        attrs = super().get_widget_attrs(bound_field, attrs, widget)

        # checkbox widgets render their label themselves
        if bound_field.widget_type == 'checkbox':
            attrs['checkbox_label'] = bound_field.label

        return attrs
