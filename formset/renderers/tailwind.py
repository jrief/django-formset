from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/default.html': 'formset/tailwind/form.html',
        'django/forms/widgets/radio.html': 'formset/tailwind/widgets/multiple_input.html',
        'formset/default/widgets/file.html': 'formset/tailwind/widgets/file.html',
        'django/forms/widgets/checkbox_select.html': 'formset/tailwind/widgets/multiple_input.html',
    })

    def _amend_label(self, context):
        context = super()._amend_label(context)
        if not isinstance(context['attrs'], dict):
            context['attrs'] = {}
        css_classes = []
        if css_class := context['attrs'].pop('class', None):
            css_classes.append(css_class)
        else:
            css_classes.append('formset-label')
        context['attrs']['class'] = ' '.join(css_classes)
        return context

    def _amend_input(self, context):
        context['widget']['attrs']['class'] = 'formset-text-input'
        return context

    def _amend_select(self, context):
        context['widget']['attrs']['class'] = 'formset-select'
        return context

    def _amend_checkbox(self, context):
        context['widget']['attrs']['class'] = 'formset-checkbox'
        return context

    def _amend_multiple_input(self, context, css_class):
        context = super()._amend_multiple_input(context)
        for _, optgroup, _ in context['widget']['optgroups']:
            for option in optgroup:
                option['template_name'] = 'formset/tailwind/widgets/input_option.html'
                option['attrs']['class'] = css_class
        return context

    def _amend_checkbox_select(self, context):
        return self._amend_multiple_input(context, 'formset-checkbox-multiple')

    def _amend_radio(self, context):
        return self._amend_multiple_input(context, 'formset-radio-select')

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_input,
        'django/forms/widgets/email.html': _amend_input,
        'django/forms/widgets/date.html': _amend_input,
        'django/forms/widgets/number.html': _amend_input,
        'django/forms/widgets/password.html': _amend_input,
        'django/forms/widgets/textarea.html': _amend_input,
        'django/forms/widgets/select.html': _amend_select,
        'django/forms/widgets/checkbox.html': _amend_checkbox,
        'django/forms/widgets/checkbox_select.html': _amend_checkbox_select,
        'django/forms/widgets/radio.html': _amend_radio,
        'formset/default/widgets/selectize.html': _amend_select,
    })
