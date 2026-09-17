from django.conf import settings

default_settings = getattr(settings, 'FORMSET_GEOMAP', {})
default_settings.setdefault('urlTemplate', 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
default_settings.setdefault('tileLayerOptions', {
    'attribution': 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
    'crossOrigin': True,
    'detectRetina': True,
    'referrerPolicy': 'strict-origin-when-cross-origin',
})
default_settings.setdefault('mapOptions', {
   'maxZoom': 18,
   'minZoom': 1,
   'zoom': 9,
   'center': [51.5, 0],  # London coordinates as default center
   'doubleClickZoom': False,
})
