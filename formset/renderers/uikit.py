from formset.boundfield import ClassList
from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    max_options_per_line = 4
    framework = 'uikit'

    def __init__(self, **kwargs):
        kwargs.setdefault('label_css_classes', 'uk-form-label')
        super().__init__(**kwargs)

    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/div.html': 'formset/uikit/form.html',
        'django/forms/widgets/checkbox.html': 'formset/uikit/widgets/checkbox.html',
        'django/forms/widgets/radio.html': 'formset/uikit/widgets/multiple_input.html',
        'django/forms/widgets/checkbox_select.html': 'formset/uikit/widgets/multiple_input.html',
        'formset/default/form.html': 'formset/uikit/form.html',
        'formset/default/collection.html': 'formset/uikit/collection.html',
        'formset/default/widgets/collection.html': 'formset/uikit/widgets/collection.html',
        'formset/default/widgets/file.html': 'formset/uikit/widgets/file.html',
    })

    def _amend_input(self, context):
        context['widget']['attrs']['class'] = ClassList('uk-input')
        return context

    def _amend_label(self, context):
        return super()._amend_label(context, hide_checkbox_label=True)

    def _amend_textarea(self, context):
        context['widget']['attrs']['class'] = ClassList('uk-textarea')
        return context

    def _amend_select(self, context):
        context['widget']['attrs']['class'] = ClassList('uk-select')
        return context

    def _amend_multiple_input(self, context):
        context = super()._amend_multiple_input(context)
        for _, optgroup, _ in context['widget']['optgroups']:
            for option in optgroup:
                option['template_name'] = 'formset/uikit/widgets/input_option.html'
        return context

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_input,
        'django/forms/widgets/email.html': _amend_input,
        'django/forms/widgets/date.html': _amend_input,
        'django/forms/widgets/number.html': _amend_input,
        'django/forms/widgets/password.html': _amend_input,
        'django/forms/widgets/textarea.html': _amend_textarea,
        'django/forms/widgets/select.html': _amend_select,
        'django/forms/widgets/checkbox_select.html': _amend_multiple_input,
        'django/forms/widgets/radio.html': _amend_multiple_input,
        'formset/default/widgets/selectize.html': _amend_select,
        'formset/default/widgets/selectize_country.html': _amend_select,
        'formset/forms/widgets/textarea.html': _amend_textarea,
    })
