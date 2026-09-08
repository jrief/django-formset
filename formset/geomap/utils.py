import json

from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.html import strip_spaces_between_tags


def amend_geojson_feature_collection(map_data):
    for feature in map_data['features']:
        identifier, index = feature['id'].split(':')
        properties = feature['properties']
        properties.update({'_marker_': {}, '_popup_': {}, '_tooltip_': {}})

        # custom Leaflet marker icon
        if feature['geometry']['type'] == 'Point':
            try:
                marker_icon = get_template(f'geomap/markers/{identifier}.json').render()
                properties['_marker_']['icon'] = json.loads(marker_icon)
            except TemplateDoesNotExist:
                pass

        # Leaflet popup
        try:
            content = get_template(f'geomap/popups/{identifier}.html').render(properties)
            properties['_popup_']['content'] = strip_spaces_between_tags(content)
            options = get_template(f'geomap/popups/{identifier}.json').render(properties)
            properties['_popup_']['options'] = json.loads(options)
        except TemplateDoesNotExist:
            pass

        # Leaflet tooltip
        try:
            content = get_template(f'geomap/tooltips/{identifier}.html').render(properties)
            properties['_tooltip_']['content'] = strip_spaces_between_tags(content)
            options = get_template(f'geomap/tooltips/{identifier}.json').render(properties)
            properties['_tooltip_']['options'] = json.loads(options)
        except TemplateDoesNotExist:
            pass
    return map_data
