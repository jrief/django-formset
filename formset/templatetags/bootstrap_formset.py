from django import template
from django.forms import Form
from django.template.loader import get_template

from formset.mixins.bootstrap4 import BootstrapErrorList, BootstrapFormMixin

register = template.Library()


@register.simple_tag
def render_groups(form, field_classes=None, label_classes=None, control_classes=None):
    assert isinstance(form, Form), "'render_groups' must be applied to a Form of type 'BootstrapFormMixin'."
    if not isinstance(form, BootstrapFormMixin):
        args = {}
        if field_classes:
            args['field_css_classes'] = field_classes
        if label_classes:
            args['label_css_classes'] = label_classes
        if control_classes:
            args['control_css_classes'] = control_classes
        form.__class__ = type(form.__class__.__name__, (BootstrapFormMixin, form.__class__), args)
        form.error_class = BootstrapErrorList
    return form.as_field_group()


@register.filter
def bootstrapify(form):
    assert isinstance(form, Form), "'bootstrapify' must be applied to a Django Form."
    if not isinstance(form, BootstrapFormMixin):
        form.__class__ = type(form.__class__.__name__, (BootstrapFormMixin, form.__class__), {})
        form.error_class = BootstrapErrorList
    return form


@register.simple_tag
def render_group(bf, template_name='formset/bootstrap4/field_group.html'):
    assert isinstance(bf.form, BootstrapFormMixin), \
        "'render_group' must be applied only to forms prepared for Bootstrap. Did you forget to use 'bootstrapify'?"
    template = get_template(template_name)
    context = {
        'auto_id': bf.auto_id,
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
