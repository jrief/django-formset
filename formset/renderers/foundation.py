from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    max_options_per_line = 4
    framework = 'foundation'

    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/div.html': 'formset/foundation/form.html',
        'django/forms/widgets/checkbox.html': 'formset/foundation/widgets/checkbox.html',
        'django/forms/widgets/radio.html': 'formset/foundation/widgets/multiple_input.html',
        'django/forms/widgets/checkbox_select.html': 'formset/foundation/widgets/multiple_input.html',
        'formset/default/form.html': 'formset/foundation/form.html',
        'formset/default/collection.html': 'formset/foundation/collection.html',
        'formset/default/widgets/collection.html': 'formset/foundation/widgets/collection.html',
        'formset/default/widgets/file.html': 'formset/foundation/widgets/file.html',
        'formset/default/widgets/dual_selector.html': 'formset/foundation/widgets/dual_selector.html',
    })

    def _amend_label(self, context):
        return super()._amend_label(context, hide_checkbox_label=True)

    def _amend_multiple_input(self, context):
        context = super()._amend_multiple_input(context)
        if context['widget'].get('inlined_options'):
            for _, optgroup, _ in context['widget']['optgroups']:
                for option in optgroup:
                    option['template_name'] = 'formset/foundation/widgets/inlined_input_option.html'
        return context

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/checkbox_select.html': _amend_multiple_input,
        'django/forms/widgets/radio.html': _amend_multiple_input,
    })
