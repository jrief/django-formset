from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/default.html': 'formset/bulma/form.html',
        'django/forms/widgets/radio.html': 'formset/bulma/widgets/multiple_input.html',
        'django/forms/widgets/select.html': 'formset/bulma/widgets/select.html',
        'formset/default/widgets/selectize.html': 'formset/bulma/widgets/select.html',
        'formset/default/widgets/file.html': 'formset/bulma/widgets/file.html',
        'django/forms/widgets/checkbox_select.html': 'formset/bulma/widgets/multiple_input.html',
    })

    def _amend_input(self, context):
        context['widget']['attrs']['class'] = 'input'
        return context

    def _amend_label(self, context):
        context = super()._amend_label(context)
        if isinstance(context['attrs'], dict):
            css_classes = []
            if css_class := context['attrs'].pop('class', None):
                css_classes.append(css_class)
            else:
                css_classes.append('label')
            context['attrs']['class'] = ' '.join(css_classes)
        else:
            context['attrs'] = {'class': 'label'}
        return context

    def _amend_multiple_input(self, context, css_class):
        context = super()._amend_multiple_input(context)
        css_classes = [css_class]
        if not context['widget'].get('inlined_options'):
            css_classes.append('is-block ml-0 mb-1')
        for _, optgroup, _ in context['widget']['optgroups']:
            for option in optgroup:
                option['template_name'] = 'formset/bulma/widgets/input_option.html'
                option['label_css_classes'] = ' '.join(css_classes)
        return context

    def _amend_checkbox_select(self, context):
        return self._amend_multiple_input(context, 'checkox mr-2')

    def _amend_radio(self, context):
        return self._amend_multiple_input(context, 'radio mr-1')

    def _amend_textarea(self, context):
        context['widget']['attrs']['class'] = 'textarea'
        return context

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_input,
        'django/forms/widgets/email.html': _amend_input,
        'django/forms/widgets/date.html': _amend_input,
        'django/forms/widgets/number.html': _amend_input,
        'django/forms/widgets/password.html': _amend_input,
        'django/forms/widgets/checkbox_select.html': _amend_checkbox_select,
        'django/forms/widgets/textarea.html': _amend_textarea,
        'django/forms/widgets/radio.html': _amend_radio,
    })
