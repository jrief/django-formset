from formset.mixins import default


class WidgetMixin(default.WidgetMixin):
    template_mapping = {
        'Select': 'formset/bulma/widgets/select.html',
        'SelectMultiple': 'formset/bulma/widgets/selectmultiple.html',
        'RadioSelect': 'formset/bulma/widgets/radio.html',
        'CheckboxInput': 'formset/bulma/widgets/checkbox.html',
        'CheckboxSelectMultiple': 'formset/bulma/widgets/checkboxselectmultiple.html',
        'UploadedFileInput': 'formset/bulma/widgets/file.html',
    }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        class_name = self.__class__.__name__
        # replace inner widget to render according to Bulma's best practice
        if class_name == 'RadioSelect':
            for group, options, _ in context['widget']['optgroups']:
                for option in options:
                    option['template_name'] = 'formset/bulma/widgets/radio_option.html'
        elif class_name == 'CheckboxSelectMultiple':
            for group, options, _ in context['widget']['optgroups']:
                for option in options:
                    option['template_name'] = 'formset/bulma/widgets/checkbox_option.html'
        return context


class FormMixin(default.CheckboxFormMixin, default.FormMixin):
    """
    Class to mix into a Django ``Form`` or ``ModelForm`` class.
    """
    field_css_classes = 'mb-2'
    label_css_classes = 'label'
    help_text_html='<p class="help">%s</p>'
    widget_mixin = WidgetMixin
    widget_css_classes = {
        'text': 'input',
        'email': 'input',
        'date': 'input',
        'checkbox': 'mr-2',
        'checkboxselectmultiple': 'mr-2',
        'radioselect': 'mr-2',
        'number': 'input',
        'textarea': 'textarea',
        'password': 'input',
    }
