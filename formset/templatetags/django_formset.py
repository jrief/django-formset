from django import template
from django.forms import BaseForm
from django.template.loader import get_template

from formset.mixins.default import FormMixin, FormsetErrorList


def _formsetify(form, form_mixin=FormMixin):
    assert isinstance(form, BaseForm), \
        "'formsetify' must be applied to a Form object inheriting from 'django.forms.BaseForm'."
    if not isinstance(form, form_mixin):
        form.__class__ = type(form.__class__.__name__, (form_mixin, form.__class__), {})
        form.error_class = FormsetErrorList
    return form


def _render_groups(form, form_mixin=FormMixin, field_classes=None, label_classes=None, control_classes=None):
    assert isinstance(form, BaseForm), \
        "'render_groups' must be applied to a Form object inheriting from 'django.forms.BaseForm'."
    if not isinstance(form, form_mixin):
        args = {}
        if field_classes:
            args['field_css_classes'] = field_classes
        if label_classes:
            args['label_css_classes'] = label_classes
        if control_classes:
            args['control_css_classes'] = control_classes
        form.__class__ = type(form.__class__.__name__, (form_mixin, form.__class__), args)
        form.error_class = FormsetErrorList
    return form.as_field_groups()


def _render_group(bf, template_name='formset/default/field_group.html'):
    assert isinstance(bf.form, FormMixin), \
        "'render_group' must be applied to a Form object inheriting from 'formset.mixins.FormMixin'."
    template = get_template(template_name)
    context = {
        'id_for_label': bf.id_for_label,
        'required': bf.field.required,
        'is_hidden': bf.is_hidden,
        'label': bf.label,
        'name': bf.name,
        'value': bf.value(),
        'widget': bf.as_widget(),
        'widget_type': bf.widget_type,
        'errors': bf.errors,
        'css_classes': bf.css_classes(),
        'help_text': bf.help_text,
    }
    return template.render(context)


register = template.Library()
register.filter('formsetify', _formsetify)
register.simple_tag(_render_groups, name='render_groups')
register.simple_tag(_render_group, name='render_group')
