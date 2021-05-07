from formset.mixins import default


class WidgetMixin(default.WidgetMixin):
    template_mapping = {
        'RadioSelect': 'formset/foundation/widgets/radio.html',
        'CheckboxInput': 'formset/foundation/widgets/checkbox.html',
        'CheckboxSelectMultiple': 'formset/foundation/widgets/checkboxselectmultiple.html',
        'UploadedFileInput': 'formset/foundation/widgets/file.html',
    }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if context.get('inlined_checks') is True:
            # replace inner widget to render according to Foundation's best practice
            for group, options, _ in context['widget']['optgroups']:
                for option in options:
                    option['template_name'] = 'formset/foundation/widgets/inlined_checks.html'
        return context


class FormMixin(default.CheckboxFormMixin, default.FormMixin):
    help_text_html='<p class="help-text">%s</p>'
    widget_mixin = WidgetMixin
