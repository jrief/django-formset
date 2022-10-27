from formset.boundfield import ClassList
from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    max_options_per_line = 4
    framework = 'bootstrap'

    def __init__(self, **kwargs):
        kwargs.setdefault('label_css_classes', 'form-label')
        super().__init__(**kwargs)

    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/default.html': 'formset/bootstrap/form.html',
        'django/forms/widgets/checkbox.html': 'formset/bootstrap/widgets/checkbox.html',
        'django/forms/widgets/radio.html': 'formset/bootstrap/widgets/multiple_input.html',
        'django/forms/widgets/checkbox_select.html': 'formset/bootstrap/widgets/multiple_input.html',
        'formset/default/widgets/dual_selector.html': 'formset/bootstrap/widgets/dual_selector.html',
        'formset/default/widgets/file.html': 'formset/bootstrap/widgets/file.html',
        'formset/default/widgets/richtextarea.html': 'formset/bootstrap/widgets/richtextarea.html',
    })

    def _amend_input(self, context):
        super()._amend_input(context)
        context['widget']['attrs']['class'].add('form-control')
        return context

    def _amend_checkbox(self, context):
        context['widget']['attrs']['class'] = ClassList('form-check-input')
        return context

    def _amend_select(self, context):
        context['widget']['attrs']['class'] = ClassList('form-select')
        return context

    def _amend_dual_selector(self, context):
        context.update(
            select_classes='form-select',
            lookup_field_classes='form-control form-control-sm',
        )
        return context

    def _amend_file(self, context):
        return context  # intentionally noop

    def _amend_label(self, context):
        return super()._amend_label(context, hide_checkbox_label=True)

    def _amend_multiple_input(self, context):
        context = super()._amend_multiple_input(context)
        for _, optgroup, _ in context['widget']['optgroups']:
            for option in optgroup:
                option['attrs']['class'] = ClassList('form-check-input')
                option['template_name'] = 'formset/bootstrap/widgets/input_option.html'
        return context

    def _amend_fieldset(self, context):
        context = super()._amend_fieldset(context)
        context.update(
            help_text_template='formset/bootstrap/help_text.html',
        )
        return context

    def _amend_collection(self, context):
        context = super()._amend_collection(context)
        context.update(
            add_collection_button='formset/bootstrap/buttons/add_collection.html',
            remove_collection_button='formset/bootstrap/buttons/remove_collection.html',
            help_text_template='formset/bootstrap/help_text.html',
        )
        return context

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_input,
        'django/forms/widgets/email.html': _amend_input,
        'django/forms/widgets/date.html': _amend_input,
        'django/forms/widgets/datetime.html': _amend_input,
        'django/forms/widgets/number.html': _amend_input,
        'django/forms/widgets/url.html': _amend_input,
        'django/forms/widgets/password.html': _amend_input,
        'django/forms/widgets/textarea.html': _amend_input,
        'django/forms/widgets/select.html': _amend_select,
        'django/forms/widgets/checkbox.html': _amend_checkbox,
        'django/forms/widgets/checkbox_select.html': _amend_multiple_input,
        'django/forms/widgets/radio.html': _amend_multiple_input,
        'formset/default/widgets/file.html': _amend_file,
        'formset/default/widgets/selectize.html': _amend_select,
        'formset/default/widgets/dual_selector.html': _amend_dual_selector,
        'formset/default/fieldset.html': _amend_fieldset,
        'formset/default/collection.html': _amend_collection,
        'formset/default/widgets/richtextarea.html': _amend_input,
    })
