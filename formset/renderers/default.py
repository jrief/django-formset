import copy
import types

from django.forms.renderers import DjangoTemplates
from django.utils.html import format_html

from formset.boundfield import ClassList


class FormRenderer(DjangoTemplates):
    """
    The form renderer used for the proper representation of elements from **django-formset**.
    """

    max_options_per_line = 0  # for multiple checkboxes and radio-selects
    exempt_feedback = False  # if True, exempt rendered field from feedback
    framework = 'default'

    _template_mapping = {
        'django/forms/errors/list/default.html': 'formset/default/field_errors.html',
        'django/forms/default.html': 'formset/default/form.html',
        'django/forms/widgets/file.html': 'formset/default/widgets/file.html',
        'django/forms/widgets/radio.html': 'formset/default/widgets/multiple_input.html',
        'django/forms/widgets/checkbox_select.html': 'formset/default/widgets/multiple_input.html',
    }

    def __init__(self, field_css_classes=None, label_css_classes=None, control_css_classes=None,
                 form_css_classes=None, fieldset_css_classes=None, collection_css_classes=None,
                 max_options_per_line=None, exempt_feedback=None):
        self.field_css_classes = field_css_classes
        self.label_css_classes = ClassList(label_css_classes)
        self.control_css_classes = ClassList(control_css_classes)
        self.form_css_classes = ClassList(form_css_classes)
        self.fieldset_css_classes = ClassList(fieldset_css_classes)
        self.collection_css_classes = ClassList(collection_css_classes)
        if max_options_per_line is not None:
            self.max_options_per_line = max_options_per_line
        if exempt_feedback is not None:
            self.exempt_feedback = exempt_feedback
        super().__init__()

    def get_template(self, template_name):
        template_name = self._template_mapping.get(template_name, template_name)
        return super().get_template(template_name)

    def _amend_form(self, context):
        context.update(
            control_css_classes=self.control_css_classes,
            form_css_classes=self.form_css_classes,
        )
        return context

    def _amend_label(self, context, hide_checkbox_label=False):
        if self.label_css_classes:
            if not isinstance(context['attrs'], dict):
                context['attrs'] = {}
            context['attrs']['class'] = ClassList(self.label_css_classes)
        if hide_checkbox_label and context['field'].widget_type == 'checkbox':
            # `<label>Label:</label>` is rendered by `{{ field }}`, so remove it to
            # prevent double rendering.
            context.pop('label', None)
            context['attrs'].pop('for', None)
            context['use_tag'] = bool(self.control_css_classes)
        return context

    def _amend_feedback(self, context):
        if self.exempt_feedback:
            context['widget']['attrs']['class'].add('dj-exempt-feedback')
        return context

    def _amend_input(self, context):
        context['widget']['attrs']['class'] = ClassList()
        self._amend_feedback(context)
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

    def _amend_fieldset(self, context):
        context.update(
            css_classes=self.fieldset_css_classes,
            help_text_template='formset/default/help_text.html',
        )
        return context

    def _amend_collection(self, context):
        context.update(
            add_collection_button='formset/default/buttons/add_collection.html',
            remove_collection_button='formset/default/buttons/remove_collection.html',
            help_text_template='formset/default/help_text.html',
            css_classes=self.collection_css_classes,
            add_collection_label=context['collection'].add_label,
        )
        return context

    _context_modifiers = {
        'django/forms/default.html': _amend_form,
        'django/forms/label.html': _amend_label,
        'django/forms/widgets/checkbox_select.html': _amend_multiple_input,
        'django/forms/widgets/radio.html': _amend_multiple_input,
        'formset/default/fieldset.html': _amend_fieldset,
        'formset/default/collection.html': _amend_collection,
    }

    @classmethod
    def _copy_context(cls, context):
        """
        Make a semi-deep copy of context. This is required since the amend-methods
        modify the context before rendering. Python's `copy.deepcopy()` doesn't work
        here, because the File field's _io.BufferedReader can't be pickled.
        """
        replica = context.copy()
        if 'attrs' in context:
            replica['attrs'] = copy.deepcopy(context['attrs'])
        if 'widget' in context:
            replica['widget'] = copy.deepcopy(context['widget'])
        return replica

    def render(self, template_name, context, request=None):
        context = self._copy_context(context)
        context_modifier = self._context_modifiers.get(template_name)
        if callable(context_modifier):
            context = types.MethodType(context_modifier, self)(context)
        template = self.get_template(template_name)
        return template.render(context, request=request).strip()


def richtext_attributes(attrs):
    """
    Converts the internal representation of node attributes into a specific string such as
    ``style="prop: value"`` or ``class="specfic-css-class"``. This is to enforce paragraph
    styling according to the CSS framework's best practice.
    """
    styles = {}
    for key, value in attrs.items():
        if not value:
            continue
        if key == 'textIndent' and value == 'indent':
            styles.update({'text-indent': '3em'})
        elif key == 'textIndent' and value == 'outdent':
            styles.update({'text-indent': '-3em', 'padding': '3em'})
        elif key == 'textMargin':
            styles.update({'margin': f'{2 * value}em'})
        elif key == 'textAlign':
            styles.update({'text-align': value})
    if styles:
        return format_html(' style="{}"', ' '.join(f'{prop}: {val};' for prop, val in styles.items()))
    return ''
