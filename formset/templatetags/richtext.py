import json

from django import template
from django.template.loader import get_template
from django.utils.html import mark_safe, strip_spaces_between_tags
from django.utils.module_loading import import_string


def render_richtext(data, doc_template='richtext/doc.html', framework='default'):
    if isinstance(data, dict):
        root_node = data
    else:
        try:
            root_node = json.loads(data)
        except json.JSONDecodeError:
            root_node = {}
    template = get_template(doc_template)
    context = {
        'node': root_node,
        'framework': framework,
        'richtext_footnotes': [],
    }
    html = template.render(context).replace('\t', '').replace('\n', '')
    return mark_safe(strip_spaces_between_tags(html))


def render_attributes(context, attrs):
    if not isinstance(attrs, dict):
        return ''
    framework = context.get('framework', 'default')
    try:
        richtext_attributes = import_string(f'formset.renderers.{framework}.richtext_attributes')
    except ImportError:
        from formset.renderers.default import richtext_attributes
    return richtext_attributes(attrs)


def render_footnote(context, footnote_ref_template, attrs):
    if not isinstance(attrs, dict):
        return ''
    context['richtext_footnotes'].append(attrs)
    template = get_template(footnote_ref_template)
    return template.render({'footnote_counter': len(context['richtext_footnotes'])})


register = template.Library()
register.simple_tag(render_richtext, name='render_richtext')
register.simple_tag(render_attributes, name='render_attributes', takes_context=True)
register.simple_tag(render_footnote, name='render_footnote', takes_context=True)
