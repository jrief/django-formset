from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms import fields, ModelForm
from django.utils.translation import gettext_lazy as _

from formset.formfields.geomap import GeoMapField
from formset.formfields.richtext import RichTextField
from formset.geomap import controls as geomap_controls, dialogs as geomap_dialogs
from formset.richtext import controls as richtext_controls
from formset.richtext.dialogs import SimpleGeoMapDialogForm, PlaceholderDialogForm, SimpleImageDialogForm
from formset.widgets.geomap import GeoMapWidget
from formset.widgets.richtext import RichTextarea

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


class RichtextDialogForm(geomap_dialogs.GeoMapDialogForm):
    title = "Edit"
    extension = 'extra_body'
    properties_map = {'body': 'body'}

    body = RichTextField()


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


class SpecialGeoMapDialogForm(SimpleGeoMapDialogForm):
    geomap = GeoMapField(
        label=_("Edit Map Markers"),
        widget=GeoMapWidget(
            controls_topleft=[
                geomap_controls.PointEditor(
                    dialog_forms=[
                        RichtextDialogForm(),
                    ],
                ),
            ],
            attrs={
                'style': 'height:300px;width:100%;',
                'richtext-map-to': '{dataset: elements.geomap.value}',
                'richtext-map-from': '{dataset: {content: JSON.stringify(attributes.dataset)}}',
            },
        ),
        required=False,
    )



class ChurchModelForm(ModelForm):
    map = GeoMapField(
        widget=GeoMapWidget(
            controls_topleft=[
                geomap_controls.PointEditor(
                    dialog_forms=[
                        geomap_dialogs.SimpleNameDialogForm(),
                    ],
                ),
                geomap_controls.PolylineEditor(
                    # dialog_forms=[
                    #     geomap_dialogs.SimpleNameDialogForm(),
                    # ],
                ),
                geomap_controls.PolygonEditor(
                    # dialog_forms=[
                    #     geomap_dialogs.SimpleNameDialogForm(),
                    # ],
                ),
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
            attrs={'style': 'height: 450px;'},
        )
    )
    body = RichTextField(
        widget=RichTextarea(
            control_elements=[
                richtext_controls.Bold(),
                richtext_controls.Italic(),
                richtext_controls.DialogControl(SpecialGeoMapDialogForm()),
                richtext_controls.DialogControl(SimpleImageDialogForm()),
                richtext_controls.Separator(),
                richtext_controls.ClearFormat(),
                richtext_controls.Redo(),
                richtext_controls.Undo(),
            ],
        )
    )

    class Meta:
        model = ChurchModel
        fields = ['body', 'map']
