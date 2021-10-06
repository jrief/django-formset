from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/default.html': 'formset/foundation/form.html',
        'django/forms/widgets/radio.html': 'formset/foundation/widgets/multiple_input.html',
        'formset/default/widgets/file.html': 'formset/foundation/widgets/file.html',
        'django/forms/widgets/checkbox_select.html': 'formset/foundation/widgets/multiple_input.html',
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
        context = super()._amend_label(context)
        # if isinstance(context['attrs'], dict):
        #     css_classes = []
        #     if css_class := context['attrs'].pop('class', None):
        #         css_classes.append(css_class)
        #     if context['field'].widget_type in ['checkbox']:
        #         css_classes = ['form-check-label']
        #     else:
        #         css_classes.append('form-label')
        #     context['attrs']['class'] = ' '.join(css_classes)
        return context

    def _amend_multiple_input(self, context):
        context = super()._amend_multiple_input(context)
        if context['widget'].get('inlined_options'):
            for _, optgroup, _ in context['widget']['optgroups']:
                for option in optgroup:
                    option['template_name'] = 'formset/foundation/widgets/inlined_input_option.html'
        return context

    _context_modifiers = {
        #'django/forms/label.html': _amend_label,
        # 'django/forms/widgets/text.html': _amend_default_widget,
        # 'django/forms/widgets/email.html': _amend_default_widget,
        # 'django/forms/widgets/file.html': _amend_default_widget,
        # 'django/forms/widgets/date.html': _amend_default_widget,
        # 'django/forms/widgets/select.html': _amend_select,
        # 'formset/default/widgets/selectize.html': _amend_select,
        # 'django/forms/widgets/number.html': _amend_default_widget,
        # 'django/forms/widgets/password.html': _amend_default_widget,
        # 'django/forms/widgets/checkbox.html': _amend_checkbox,
        'django/forms/widgets/checkbox_select.html': _amend_multiple_input,
        # 'formset/default/widgets/file.html': _amend_file,
        'django/forms/widgets/radio.html': _amend_multiple_input,
    }
