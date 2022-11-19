import json

from django import template
from django.template.loader import get_template
from django.utils.html import mark_safe


def render_richtext(data, doc_template='richtext/doc.html'):
    context = data if isinstance(data, dict) else json.loads(data)
    template = get_template(doc_template)
    html = template.render({'node': context}).replace('\t', '').replace('\n', '')
    return mark_safe(html)

register = template.Library()
register.simple_tag(render_richtext, name='render_richtext')
