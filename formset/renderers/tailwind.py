from formset.boundfield import ClassList
from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    max_options_per_line = 4
    framework = 'tailwind'

    def __init__(self, **kwargs):
        kwargs.setdefault('label_css_classes', 'formset-label')
        super().__init__(**kwargs)

    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/default.html': 'formset/tailwind/form.html',
        'django/forms/widgets/checkbox.html': 'formset/tailwind/widgets/checkbox.html',
        'django/forms/widgets/radio.html': 'formset/tailwind/widgets/multiple_input.html',
        'formset/default/widgets/dual_selector.html': 'formset/tailwind/widgets/dual_selector.html',
        'formset/default/widgets/file.html': 'formset/tailwind/widgets/file.html',
        'django/forms/widgets/checkbox_select.html': 'formset/tailwind/widgets/multiple_input.html',
    })

    def _amend_label(self, context):
        return super()._amend_label(context, hide_checkbox_label=True)

    def _amend_text_input(self, context):
        context['widget']['attrs']['class'] = ClassList('formset-text-input')
        return context

    def _amend_email_input(self, context):
        context['widget']['attrs']['class'] = ClassList('formset-email-input')
        return context

    def _amend_date_input(self, context):
        context['widget']['attrs']['class'] = ClassList('formset-date-input')
        return context

    def _amend_number_input(self, context):
        context['widget']['attrs']['class'] = ClassList('formset-number-input')
        return context

    def _amend_password_input(self, context):
        context['widget']['attrs']['class'] = ClassList('formset-password-input')
        return context

    def _amend_textarea(self, context):
        context['widget']['attrs']['class'] = ClassList('formset-textarea')
        return context

    def _amend_select(self, context):
        if context['widget']['attrs'].get('multiple') is True:
            context['widget']['attrs']['class'] = ClassList('formset-select-multiple')
        else:
            context['widget']['attrs']['class'] = ClassList('formset-select')
        return context

    def _amend_dual_selector(self, context):
        context.update(
            select_classes=ClassList('formset-dual-selector-select'),
            lookup_field_classes=ClassList('formset-dual-selector-lookup'),
        )
        return context

    def _amend_checkbox(self, context):
        context['widget']['attrs']['class'] = ClassList('formset-checkbox')
        return context

    def _amend_multiple_input(self, context, css_class):
        context = super()._amend_multiple_input(context)
        for _, optgroup, _ in context['widget']['optgroups']:
            for option in optgroup:
                option['template_name'] = 'formset/tailwind/widgets/input_option.html'
                option['attrs']['class'] = ClassList(css_class)
        return context

    def _amend_checkbox_select(self, context):
        return self._amend_multiple_input(context, 'formset-checkbox-multiple')

    def _amend_radio(self, context):
        return self._amend_multiple_input(context, 'formset-radio-select')

    def _amend_fieldset(self, context):
        context = super()._amend_fieldset(context)
        context.update(
            help_text_template='formset/tailwind/help_text.html',
        )
        return context

    def _amend_collection(self, context):
        context = super()._amend_collection(context)
        context.update(
            add_collection_button='formset/tailwind/buttons/add_collection.html',
            remove_collection_button='formset/tailwind/buttons/remove_collection.html',
            help_text_template='formset/tailwind/help_text.html',
        )
        return context

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_text_input,
        'django/forms/widgets/email.html': _amend_email_input,
        'django/forms/widgets/date.html': _amend_date_input,
        'django/forms/widgets/number.html': _amend_number_input,
        'django/forms/widgets/password.html': _amend_password_input,
        'django/forms/widgets/textarea.html': _amend_textarea,
        'django/forms/widgets/select.html': _amend_select,
        'django/forms/widgets/checkbox.html': _amend_checkbox,
        'django/forms/widgets/checkbox_select.html': _amend_checkbox_select,
        'django/forms/widgets/radio.html': _amend_radio,
        'formset/default/widgets/selectize.html': _amend_select,
        'formset/default/widgets/dual_selector.html': _amend_dual_selector,
        'formset/default/fieldset.html': _amend_fieldset,
        'formset/default/collection.html': _amend_collection,
        'formset/default/widgets/richtextarea.html': _amend_textarea,
    })
