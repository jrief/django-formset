import copy
import types

from django.forms.renderers import DjangoTemplates


class FormRenderer(DjangoTemplates):
    max_options_per_line = 4

    _template_mapping = {
        'django/forms/errors/list/default.html': 'formset/default/field_errors.html',
        'django/forms/default.html': 'formset/default/form.html',
        'django/forms/label.html': 'formset/default/label.html',
        'django/forms/widgets/radio.html': 'formset/default/widgets/multiple_input.html',
        'django/forms/widgets/file.html': 'formset/default/widgets/file.html',
        'django/forms/widgets/checkbox_select.html': 'formset/default/widgets/multiple_input.html',
    }

    def get_template(self, template_name):
        template_name = self._template_mapping.get(template_name, template_name)
        return super().get_template(template_name)

    def _amend_label(self, context):
        if label_css_classes := getattr(context['field'].form, 'label_css_classes', None):
            if not isinstance(context['attrs'], dict):
                context['attrs'] = {}
            context['attrs']['class'] = label_css_classes
        return context

    def _amend_multiple_input(self, context):
        """
        Inlines a small number of radio/checkbox fields to render them on one line.
        """
        max_options = 0
        for group, options, index in context['widget']['optgroups']:
            if group is None:
                max_options = len(context['widget']['optgroups'])
                break
            max_options = max(max_options, len(options))
        context['widget']['inlined_options'] = max_options <= self.max_options_per_line
        return context

    _context_modifiers = {
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/checkbox_select.html': _amend_multiple_input,
        'django/forms/widgets/radio.html': _amend_multiple_input,
    }

    def render(self, template_name, context, request=None):
        context = copy.deepcopy(context)
        context_modifier = self._context_modifiers.get(template_name)
        if callable(context_modifier):
            context = types.MethodType(context_modifier, self)(context)
        template = self.get_template(template_name)
        return template.render(context, request=request).strip()
