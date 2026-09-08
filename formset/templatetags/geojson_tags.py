import json
from urllib.parse import quote

from django import template
from django.http import HttpRequest
from django.template.loader import get_template
from django.utils.html import strip_spaces_between_tags
from django.utils.safestring import mark_safe

from formset.geomap.utils import amend_geojson_feature_collection


register = template.Library()

@register.simple_tag(name='render_geojson', takes_context=True)
def render_geojson(context, map_data, template='geomap/geojson-renderer.html', leaflet_attributes=None, filter='true', style=None):
    try:
        amend_geojson_feature_collection(map_data)
    except (KeyError, TypeError):
        raise ValueError("map_data must be valid GeoJSON")
    default_style = {'width': '100%', 'display': 'block'}
    try:
        style = {**default_style, **dict(item.split(':') for item in style.split(';') if item)}
    except AttributeError:
        style = default_style
    request = context.get('request', HttpRequest())
    template = get_template(template)
    context = {
        'json_data': json.dumps(map_data),
        'filter': quote(filter),
        'style': '; '.join(f'{k}: {v}' for k, v in style.items()),
        'leaflet_attributes': leaflet_attributes,
    }
    html = template.render(context, request)
    return mark_safe(strip_spaces_between_tags(html))
