from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/default.html': 'formset/bootstrap/form.html',
        'django/forms/widgets/radio.html': 'formset/bootstrap/widgets/radio.html',
        'formset/default/widgets/file.html': 'formset/bootstrap/widgets/file.html',
        'django/forms/widgets/checkbox.html': 'formset/default/widgets/input.html',
        'django/forms/widgets/checkbox_select.html': 'formset/bootstrap/widgets/checkbox_select.html',
    })

    def _amend_default_widget(self, context):
        context['widget']['attrs']['class'] = 'form-control'
        return context

    def _amend_checkbox(self, context):
        context['widget']['attrs']['class'] = 'form-check-input'
        return context

    def _amend_select(self, context):
        context['widget']['attrs']['class'] = 'form-select'
        return context

    def _amend_file(self, context):
        return context  # intentionally noop

    def _amend_label(self, context):
        if isinstance(context['attrs'], dict):
            if context['field'].widget_type in ['checkbox']:
                context['attrs']['class'] = 'form-check-label'
            else:
                context['attrs']['class'] = 'form-label'
        return context

    def _amend_multiple_input(self, context):
        context = super()._amend_multiple_input(context)
        for _, optgroup, _ in context['widget']['optgroups']:
            for option in optgroup:
                option['attrs']['class'] = 'form-check-input'
        return context

    _context_modifiers = {
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_default_widget,
        'django/forms/widgets/email.html': _amend_default_widget,
        'django/forms/widgets/file.html': _amend_default_widget,
        'django/forms/widgets/date.html': _amend_default_widget,
        'django/forms/widgets/select.html': _amend_select,
        'django/forms/widgets/number.html': _amend_default_widget,
        'django/forms/widgets/password.html': _amend_default_widget,
        'django/forms/widgets/checkbox.html': _amend_checkbox,
        'django/forms/widgets/checkbox_select.html': _amend_multiple_input,
        'formset/default/widgets/file.html': _amend_file,
        'django/forms/widgets/radio.html': _amend_multiple_input,
    }
