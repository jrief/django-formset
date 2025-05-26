import types

from django import template
from django.forms import BaseForm
from django.forms.models import BaseModelForm
from django.middleware.csrf import get_token
from django.template.exceptions import TemplateSyntaxError
from django.utils.module_loading import import_string

from formset.forms import DeclarativeFieldsetMetaclass, FormMixin, FormsetModelFormMetaclass
from formset.renderers.default import FormRenderer
from formset.utils import FormsetErrorList


def _formsetify(form, *args, **kwargs):
    assert isinstance(form, BaseForm), \
        "Must be applied to a Form object inheriting from 'django.forms.BaseForm'."
    if not isinstance(form, FormMixin):
        if isinstance(form, BaseModelForm):
            metaclass = FormsetModelFormMetaclass
        elif isinstance(form, BaseForm):
            metaclass = DeclarativeFieldsetMetaclass
        else:
            raise TemplateSyntaxError("Must be applied to a Form object inheriting from 'django.forms.BaseForm'.")
        form.__class__ = types.new_class(
            name=form.__class__.__name__,
            bases=(FormMixin, form.__class__),
            kwds={'metaclass': metaclass}
        )

    renderer_args = [
        ('form_css_classes', kwargs.pop('form_classes', None)),
        ('fieldset_css_classes', kwargs.pop('fieldset_classes', None)),
        ('field_css_classes', kwargs.pop('field_classes', None)),
        ('label_css_classes', kwargs.pop('label_classes', None)),
        ('control_css_classes', kwargs.pop('control_classes', None)),
        ('form_css_classes', kwargs.pop('form_classes', None)),
        ('collection_css_classes', kwargs.pop('collection_classes', None)),
        ('max_options_per_line', kwargs.pop('max_options_per_line', None)),
    ]
    if len(kwargs):
        raise TemplateSyntaxError(f"Unknown argument '{kwargs.popitem()[0]}' in formsetify.")
    renderer_kwargs = {key: value for key, value in renderer_args if value is not None}

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


def formsetify(context, form, *args, **kwargs):
    get_token(context['request'])  # ensures that the CSRF-Cookie is set
    _formsetify(form, *args, **kwargs)
    return ''


def render_form(context, form, *args, **kwargs):
    get_token(context['request'])  # ensures that the CSRF-Cookie is set
    form = _formsetify(form, *args, **kwargs)
    return form.render(template_name='formset/default/form.html')


register = template.Library()
register.simple_tag(formsetify, name='formsetify', takes_context=True)
register.simple_tag(render_form, name='render_form', takes_context=True)
