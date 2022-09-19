import json

from django import template
from django.template.loader import get_template


def render_richtext(data):
    context = data if isinstance(data, dict) else json.loads(data)
    template = get_template('richtext/doc.html')
    return template.render({'node': context})

register = template.Library()
register.simple_tag(render_richtext, name='render_richtext')
