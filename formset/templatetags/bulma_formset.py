from django import template

from formset.mixins import bulma
from .django_formset import _formsetify, _form_attrs, _render_group, _render_groups

register = template.Library()


@register.filter
def formsetify(form):
    return _formsetify(form, bulma.FormMixin)


@register.simple_tag
def form_attrs(form):
    return _form_attrs(form, bulma.FormMixin)


@register.simple_tag
def render_groups(form, field_classes=None, label_classes=None, control_classes=None):
    return _render_groups(form, bulma.FormMixin, field_classes, label_classes, control_classes)


@register.simple_tag
def render_group(bf, template_name='formset/bulma/field_group.html'):
    return _render_group(bf, template_name)
