from formset.boundfield import ClassList
from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    max_options_per_line = 4
    framework = 'bulma'

    def __init__(self, **kwargs):
        kwargs.setdefault('label_css_classes', 'label')
        super().__init__(**kwargs)

    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/div.html': 'formset/bulma/form.html',
        'django/forms/widgets/checkbox.html': 'formset/bulma/widgets/checkbox.html',
        'django/forms/widgets/radio.html': 'formset/bulma/widgets/multiple_input.html',
        'django/forms/widgets/select.html': 'formset/bulma/widgets/select.html',
        'django/forms/widgets/checkbox_select.html': 'formset/bulma/widgets/multiple_input.html',
        'formset/default/form.html': 'formset/bulma/form.html',
        'formset/default/collection.html': 'formset/bulma/collection.html',
        'formset/default/widgets/collection.html': 'formset/bulma/widgets/collection.html',
        'formset/default/widgets/selectize.html': 'formset/bulma/widgets/select.html',
        'formset/default/widgets/file.html': 'formset/bulma/widgets/file.html',
        'formset/default/widgets/dual_selector.html': 'formset/bulma/widgets/dual_selector.html',
    })

    def _amend_input(self, context):
        context['widget']['attrs']['class'] = ClassList('input')
        return context

    def _amend_label(self, context):
        return super()._amend_label(context, hide_checkbox_label=True)

    def _amend_multiple_input(self, context, css_class):
        context = super()._amend_multiple_input(context)
        label_css_classes = ClassList(css_class)
        if not context['widget'].get('inlined_options'):
            label_css_classes.add('is-block ml-0 mb-1')
        for _, optgroup, _ in context['widget']['optgroups']:
            for option in optgroup:
                option['template_name'] = 'formset/bulma/widgets/input_option.html'
                option['label_css_classes'] = label_css_classes
        return context

    def _amend_checkbox_select(self, context):
        return self._amend_multiple_input(context, 'checkbox mr-2')

    def _amend_radio(self, context):
        return self._amend_multiple_input(context, 'radio mr-1')

    def _amend_textarea(self, context):
        context['widget']['attrs']['class'] = ClassList('textarea')
        return context

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_input,
        'django/forms/widgets/email.html': _amend_input,
        'django/forms/widgets/date.html': _amend_input,
        'django/forms/widgets/number.html': _amend_input,
        'django/forms/widgets/password.html': _amend_input,
        'django/forms/widgets/url.html': _amend_input,
        'django/forms/widgets/checkbox_select.html': _amend_checkbox_select,
        'django/forms/widgets/textarea.html': _amend_textarea,
        'django/forms/widgets/radio.html': _amend_radio,
        'formset/default/widgets/date.html': _amend_input,
        'formset/default/widgets/datetime.html': _amend_input,
        'formset/default/widgets/richtextarea.html': _amend_textarea,
    })
