from django import template

from formset.mixins import foundation
from .django_formset import _formsetify, _render_group, _render_groups, _render_error_placeholder

register = template.Library()


@register.filter
def formsetify(form):
    return _formsetify(form, foundation.FormMixin)


@register.simple_tag
def render_groups(form, field_classes=None, label_classes=None, control_classes=None):
    return _render_groups(form, foundation.FormMixin, field_classes, label_classes, control_classes)


@register.simple_tag
def render_group(bf, template_name='formset/foundation/field_group.html'):
    return _render_group(bf, template_name)


@register.simple_tag
def render_error_placeholder():
    return _render_error_placeholder()
