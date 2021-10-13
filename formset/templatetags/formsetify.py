from django import template
from django.forms import BaseForm
from django.template.exceptions import TemplateSyntaxError
from django.utils.html import format_html_join
from django.utils.module_loading import import_string

from formset.utils import FormMixin, FormsetErrorList
from formset.renderers.default import FormRenderer


def _formsetify(form, *args, **kwargs):
    assert isinstance(form, BaseForm), \
        "Must be applied to a Form object inheriting from 'django.forms.BaseForm'."
    if not isinstance(form, FormMixin):
        form.__class__ = type(form.__class__.__name__, (FormMixin, form.__class__), {})
    if len(args) == 1 and args[0]:
        framework = args[0].replace('.', '').lower()  # for safety reasons
        form.renderer = import_string(f'formset.renderers.{framework}.FormRenderer')()
    elif not isinstance(form.renderer, FormRenderer):
        form.renderer = FormRenderer()
    form.error_class = FormsetErrorList
    if 'field_classes' in kwargs and not hasattr(form, 'field_css_classes'):
        form.field_css_classes = kwargs.pop('field_classes')
    if 'label_classes' in kwargs and not hasattr(form, 'label_css_classes'):
        form.label_css_classes = kwargs.pop('label_classes')
    if 'control_classes' in kwargs and not hasattr(form, 'control_css_classes'):
        form.control_css_classes = kwargs.pop('control_classes')
    if len(kwargs):
        raise TemplateSyntaxError(f"Unknown argument '{kwargs.popitem()[0]}' in formsetify.")
    return form


def _form_attrs(form, *args, **kwargs):
    form = _formsetify(form, *args, **kwargs)
    attrs = []
    form_name = getattr(form, 'name', None)
    if form_name:
        attrs.append(('name', form_name))
    if form.form_id:
        attrs.append(('id', form.form_id))
    return format_html_join('', ' {0}="{1}"', attrs)


def _render_form(form, *args, **kwargs):
    form = _formsetify(form, *args, **kwargs)
    return str(form)


register = template.Library()
register.simple_tag(_form_attrs, name='form_attrs')
register.simple_tag(_render_form, name='render_form')
