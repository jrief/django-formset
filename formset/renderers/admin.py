from formset.boundfield import ClassList
from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    max_options_per_line = 2

    def __init__(self, **kwargs):
        kwargs.setdefault('form_css_classes', ClassList('module aligned'))
        super().__init__(**kwargs)

    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/div.html': 'formset/admin/form.html',
        'formset/default/collection.html': 'formset/admin/collection.html',
        'formset/default/fieldset.html': 'formset/admin/fieldset.html',
        'formset/default/widgets/file.html': 'formset/admin/widgets/file.html',
        'formset/default/widgets/dual_selector.html': 'formset/admin/widgets/dual_selector.html',
    })

    def _amend_form(self, context):
        super()._amend_form(context)
        context['field_group_template'] = 'formset/admin/field_group.html'
        return context

    def _amend_label(self, context):
        super()._amend_label(context, hide_checkbox_label=False)
        class_list = ClassList(context['attrs'].get('class'))
        if context['field'].field.required:
            class_list.add('required')
        if context['field'].widget_type == 'checkbox':
            class_list.add('vCheckboxLabel')
        context['attrs']['class'] = class_list
        return context

    def _amend_input(self, context):
        super()._amend_input(context)
        context['widget']['attrs']['class'].add('vTextField')
        return context

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/div.html': _amend_form,
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_input,
        'formset/default/widgets/datetime.html': _amend_input,
    })
