from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms import fields, ModelForm

from formset.formfields.richtext import RichTextField
from formset.geomap import controls as geomap_controls, dialogs as geomap_dialogs
from formset.widgets.geomap import GeoMapWidget

from testapp.models import ChurchModel


initial_geojson = {
    'type': 'FeatureCollection',
    'bbox': [
        10.126647949218752,
        46.70973594407157,
        12.47222900390625,
        47.824220149350246
    ],
    'features': [
        {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [-0.127758, 51.507351],
            },
            'properties': {
                'simple_name': {
                    'name': 'London'
                },
            }
        },
        {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [2.352222, 48.856613],
            },
            'properties': {
                'simple_name': {
                    'name': 'Paris'
                },
            }
        },
        {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [13.404954, 52.520008],
            },
            'properties': {
                'simple_name': {
                    'name': 'Berlin'
                },
            }
        },
    ],
}


class ChurchDialogForm(geomap_dialogs.GeoMapDialogForm):
    title = "Edit Capacity"
    extension = 'capacity'
    properties_map = {'max_visitors': 'max_visitors', 'body': 'body'}
    icon = 'testapp/icons/users.svg'

    max_visitors = fields.IntegerField()
    body = RichTextField()


church_marker = {
    'iconUrl': staticfiles_storage.url('testapp/geomap-markers/church.svg'),
    'iconSize': [32, 32],
    'iconAnchor': [16, 35],
    'popupAnchor': [0, -28],
}


class ChurchModelForm(ModelForm):
    class Meta:
        model = ChurchModel
        fields = ['map']
        widgets = {
            'map': GeoMapWidget(
                controls_topleft=[
                    geomap_controls.PointEditor(
                        dialog_forms=[
                            geomap_dialogs.SimpleNameDialogForm(),
                        ],
                        min_markers=1,
                        max_markers=3,
                    ),
                    geomap_controls.PolylineEditor(),
                    [
                        geomap_controls.PolygonEditor(),
                        geomap_controls.MultiPolygonEditor(),
                    ],
                ],
                controls_topright=[
                    geomap_controls.PointEditor(
                        identifier='church_editor',
                        add_button_icon='testapp/icons/add-church-marker.svg',
                        marker=church_marker,
                        dialog_forms=[
                            ChurchDialogForm(),
                        ],
                    ),
                ],
                attrs={'style': 'height: 550px;'},
            )
        }
