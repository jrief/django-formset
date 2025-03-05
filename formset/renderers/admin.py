from formset.boundfield import ClassList
from formset.renderers.default import FormRenderer as DefaultFormRenderer


class FormRenderer(DefaultFormRenderer):
    max_options_per_line = 4

    def __init__(self, **kwargs):
        kwargs.setdefault('form_css_classes', ClassList('module aligned'))
        super().__init__(**kwargs)

    _template_mapping = dict(DefaultFormRenderer._template_mapping, **{
        'django/forms/div.html': 'formset/admin/form.html',
        'formset/default/widgets/file.html': 'formset/admin/widgets/file.html',
    })

    def _amend_label(self, context, **kwargs):
        super()._amend_label(context, **kwargs)
        if context['field'].field.required:
            class_list = ClassList(context['attrs'].get('class'))
            class_list.add('required')
            context['attrs']['class'] = class_list
        return context

    def _amend_input(self, context):
        super()._amend_input(context)
        context['widget']['attrs']['class'].add('vTextField')
        return context

    _context_modifiers = dict(DefaultFormRenderer._context_modifiers, **{
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/text.html': _amend_input,
    })
