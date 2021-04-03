from django import template

from formset.mixins.foundation import FoundationFormMixin
from .django_formset import _formsetify, _render_group, _render_groups

register = template.Library()


@register.filter
def formsetify(form):
    return _formsetify(form, FoundationFormMixin)


@register.simple_tag
def render_groups(form, field_classes=None, label_classes=None, control_classes=None):
    return _render_groups(form, FoundationFormMixin, field_classes, label_classes, control_classes)


@register.simple_tag
def render_group(bf, template_name='formset/foundation/field_group.html'):
    return _render_group(bf, template_name)
