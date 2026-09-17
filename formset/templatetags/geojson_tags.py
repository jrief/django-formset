import json
from urllib.parse import quote

from django import template
from django.http import HttpRequest
from django.template.loader import get_template
from django.utils.html import strip_spaces_between_tags
from django.utils.safestring import mark_safe

from formset.geomap.settings import default_settings
from formset.geomap.utils import amend_geojson_feature_collection


register = template.Library()

@register.simple_tag(name='render_geojson', takes_context=True)
def render_geojson(
    context,
    map_data,
    template='geomap/geojson-renderer.html',
    filter='true',
    style=None,
    url_template=None,
    tile_layer_options=None,
    map_options=None,
):
    try:
        amend_geojson_feature_collection(map_data)
    except (KeyError, TypeError):
        raise ValueError("map_data must be valid GeoJSON")
    default_style = {'width': '100%', 'display': 'block'}
    try:
        style = {**default_style, **dict(item.split(':') for item in style.split(';') if item)}
    except AttributeError:
        style = default_style
    if url_template is None:
        url_template = default_settings['urlTemplate']
    if tile_layer_options is None:
        tile_layer_options = default_settings['tileLayerOptions']
    if map_options is None:
        map_options = default_settings['mapOptions']
    request = context.get('request', HttpRequest())
    template = get_template(template)
    context = {
        'content': json.dumps(map_data),
        'filter': quote(filter),
        'style': '; '.join(f'{k}: {v}' for k, v in style.items()),
        'url_template': url_template,
        'tile_layer_options': json.dumps(tile_layer_options),
        'map_options': json.dumps(map_options),
    }
    html = template.render(context, request)
    return mark_safe(strip_spaces_between_tags(html))
