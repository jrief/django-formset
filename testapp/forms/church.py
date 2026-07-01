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


class ChurchModelForm(ModelForm):
    map = GeoMapField(
        widget=GeoMapWidget(
            controls_topleft=[
                controls.PointEditor(dialog_forms=[
                    dialogs.SimpleNameDialogForm(),
                    CapacityDialogForm(),
                ]),
            ],
            attrs={'style': 'height: 600px;'},
        )
    )

    class Meta:
        model = ChurchModel
        fields = '__all__'
