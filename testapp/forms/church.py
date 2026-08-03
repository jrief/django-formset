from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms import fields, ModelForm

from formset.formfields.geomap import GeoMapField
from formset.geomap import controls, dialogs
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


class CapacityDialogForm(dialogs.GeoMapDialogForm):
    title = "Edit Capacity"
    extension = 'capacity'
    properties_map = {'max_visitors': 'max_visitors'}
    icon = 'testapp/icons/users.svg'

    max_visitors = fields.IntegerField()


church_marker = {
    'iconUrl': staticfiles_storage.url('testapp/geomap-markers/church.svg'),
    'iconSize': [32, 32],
    'iconAnchor': [16, 35],
    'popupAnchor': [0, -28],
}


class ChurchModelForm(ModelForm):
    map = GeoMapField(
        widget=GeoMapWidget(
            controls_topleft=[
                controls.PointEditor(
                    # dialog_forms=[
                    #     dialogs.SimpleNameDialogForm(),
                    # ],
                ),
                controls.PolylineEditor(
                    # dialog_forms=[
                    #     dialogs.SimpleNameDialogForm(),
                    # ],
                ),
                controls.PolygonEditor(
                    dialog_forms=[
                        dialogs.SimpleNameDialogForm(),
                    ],
                ),
            ],
            controls_topright=[
                controls.PointEditor(
                    identifier='point_editor_2',
                    button_icon='testapp/icons/church-marker.svg',
                    marker=church_marker,
                    dialog_forms=[
                        dialogs.SimpleNameDialogForm(extension='simple_name_2'),
                        CapacityDialogForm(),
                    ],
                ),
            ],
            attrs={'style': 'height: 600px;'},
        )
    )

    class Meta:
        model = ChurchModel
        fields = '__all__'
