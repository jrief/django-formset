from django.forms import fields, models, widgets

from formset.widgets import Selectize
from formset.formfields.geomap import GeoMapField
from formset.formfields.richtext import RichTextField
from formset.geomap.controls import PointEditor
from formset.geomap.dialogs import GeoMapDialogForm
from formset.richtext import controls as richtext_controls
from formset.richtext import dialogs as richtext_dialogs
from formset.widgets.geomap import GeoMapWidget
from formset.widgets.richtext import RichTextarea

from testapp.models.page import PageModel


class CustomHyperlinkDialogForm(richtext_dialogs.RichtextDialogForm):
    title = "Edit Hyperlink"
    extension = 'custom_hyperlink'
    extension_script = 'testapp/tiptap-extensions/custom_hyperlink.js'
    icon = 'formset/richtext/icons/link.svg'
    plugin_type = 'mark'

    text = fields.CharField(
        label="Link Text",
        widget=widgets.TextInput(attrs={
            'richtext-selection': True,
            'size': 50,
        })
    )
    link_type = fields.ChoiceField(
        label="Link Type",
        choices=[
            ('external', "External URL"),
            ('internal', "Internal Page"),
        ],
        initial='internal',
        widget=widgets.Select(attrs={
            'richtext-map-from': '{value: attributes.href ? "external" : "internal"}',
        }),
    )
    url = fields.URLField(
        label="External URL",
        widget=widgets.URLInput(attrs={
            'size': 50,
            'richtext-map-to': '{href: elements.link_type.value == "external" ? elements.url.value : ""}',
            'richtext-map-from': 'href',
            'df-show': '.link_type == "external"',
            'df-require': '.link_type == "external"',
        }),
    )
    page = models.ModelChoiceField(
        queryset=PageModel.objects.all(),
        label="Internal Page",
        widget=Selectize(attrs={
            'richtext-map-to': '{page_id: elements.link_type.value == "internal" ? elements.page.value : ""}',
            'richtext-map-from': 'page_id',
            'df-show': '.link_type == "internal"',
            'df-require': '.link_type == "internal"',
        }),
    )


class EditMarkerDialogForm(GeoMapDialogForm):
    title = "Edit Marker"
    extension = 'special_marker'
    properties_map = {'body': 'body'}

    body = RichTextField(
        widget=RichTextarea(
            control_elements=[
                richtext_controls.Bold(),
                richtext_controls.Italic(),
                richtext_controls.BulletList(),
                richtext_controls.OrderedList(),
                richtext_controls.DialogControl(CustomHyperlinkDialogForm()),
                richtext_controls.Separator(),
                richtext_controls.ClearFormat(),
                richtext_controls.Undo(),
                richtext_controls.Redo(),
            ],
            attrs={'maxlength': 500, 'style': 'height: 250px;'},
        )
    )


class SpecialGeoMapDialogForm(richtext_dialogs.SimpleGeoMapDialogForm):
    geomap = GeoMapField(
        label="Edit Map Markers",
        widget=GeoMapWidget(
            controls_topleft=[
                PointEditor(
                    dialog_forms=[
                        EditMarkerDialogForm(),
                    ],
                ),
            ],
            attrs={
                'style': 'height:300px;width:100%;',
                'richtext-map-to': '{content: elements.geomap.value}',
                'richtext-map-from': '{dataset: {content: JSON.stringify(attributes.content)}}',
            },
        ),
        required=False,
    )
