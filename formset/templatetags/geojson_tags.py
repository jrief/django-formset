import json
from urllib.parse import quote

from django import template
from django.http import HttpRequest
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.html import mark_safe, strip_spaces_between_tags


register = template.Library()

@register.simple_tag(name='render_geojson', takes_context=True)
def render_geojson(context, map_data, template='geomap/geojson-renderer.html', leaflet_attributes=None, filter='true'):
    try:
        for feature in map_data['features']:
            identifier, index = feature['id'].split(':')
            properties = feature.pop('properties')
            feature['properties'] = {'marker': {}, 'popup': {}, 'tooltip': {}}

            # custom Leaflet marker icon
            if feature['geometry']['type'] == 'Point':
                try:
                    marker_icon = get_template(f'geomap/markers/{identifier}.json').render()
                    feature['properties']['marker']['icon'] = json.loads(marker_icon)
                except TemplateDoesNotExist:
                    pass

            # Leaflet popup
            try:
                content = get_template(f'geomap/popups/{identifier}.html').render(properties)
                feature['properties']['popup']['content'] = strip_spaces_between_tags(content)
                options = get_template(f'geomap/popups/{identifier}.json').render(properties)
                feature['properties']['popup']['options'] = json.loads(options)
            except TemplateDoesNotExist:
                pass

            # Leaflet tooltip
            try:
                content = get_template(f'geomap/tooltips/{identifier}.html').render(properties)
                feature['properties']['tooltip']['content'] = strip_spaces_between_tags(content)
                options = get_template(f'geomap/tooltips/{identifier}.json').render(properties)
                feature['properties']['tooltip']['options'] = json.loads(options)
            except TemplateDoesNotExist:
                pass

    except (KeyError, TypeError):
        raise ValueError("map_data must be valid GeoJSON")

    request = context.get('request', HttpRequest())
    template = get_template(template)
    context = {
        'json_data': json.dumps(map_data),
        'leaflet_attributes': leaflet_attributes,
        'filter': quote(filter),
    }
    html = template.render(context, request)
    return mark_safe(strip_spaces_between_tags(html))
