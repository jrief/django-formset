from django import template
from django.forms import BaseForm
from django.middleware.csrf import get_token
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

    renderer_kwargs = {
        'field_css_classes': kwargs.pop('field_classes', None),
        'label_css_classes': kwargs.pop('label_classes', None),
        'control_css_classes': kwargs.pop('control_classes', None),
        'form_css_classes': kwargs.pop('form_classes', None),
        'max_options_per_line': kwargs.pop('max_options_per_line', None),
    }
    if len(kwargs):
        raise TemplateSyntaxError(f"Unknown argument '{kwargs.popitem()[0]}' in formsetify.")

    if len(args) == 1 and args[0]:
        framework = args[0].lower()
        if '.' in framework:
            form.renderer = import_string(f'{framework}.FormRenderer')(**renderer_kwargs)
        else:
            form.renderer = import_string(f'formset.renderers.{framework}.FormRenderer')(**renderer_kwargs)
    elif not isinstance(form.renderer, FormRenderer):
        form.renderer = FormRenderer(**renderer_kwargs)
    form.error_class = FormsetErrorList
    return form


def _form_attrs(context, form, *args, **kwargs):
    get_token(context['request'])  # ensures that the CSRF-Cookie is set
    form = _formsetify(form, *args, **kwargs)
    attrs = []
    form_name = getattr(form, 'name', None)
    if form_name:
        attrs.append(('name', form_name))
    if form.form_id:
        attrs.append(('id', form.form_id))
    return format_html_join('', ' {0}="{1}"', attrs)


def _render_form(context, form, *args, **kwargs):
    get_token(context['request'])  # ensures that the CSRF-Cookie is set
    form = _formsetify(form, *args, **kwargs)
    return str(form)


register = template.Library()
register.simple_tag(_form_attrs, name='form_attrs', takes_context=True)
register.simple_tag(_render_form, name='render_form', takes_context=True)
