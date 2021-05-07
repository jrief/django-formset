from formset.mixins import default


class WidgetMixin(default.WidgetMixin):
    template_mapping = {
        'RadioSelect': 'formset/bootstrap/widgets/radio.html',
        'CheckboxInput': 'formset/bootstrap/widgets/checkbox.html',
        'CheckboxSelectMultiple': 'formset/bootstrap/widgets/checkboxselectmultiple.html',
        'UploadedFileInput': 'formset/bootstrap/widgets/file.html',
    }


class FormMixin(default.CheckboxFormMixin, default.FormMixin):
    field_css_classes = 'form-group'
    checkbox_label_html = '<div class="{label_css_classes}"></div>'
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
