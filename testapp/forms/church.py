from django import forms

from formset.formfields.geomap import GeoMapField
from formset.widgets.geomap import GeoMapWidget
from formset.geomap.dialogs import SimpleNameDialogForm


class ChurchForm(forms.Form):
    map = GeoMapField(
        widget=GeoMapWidget(
            controls_topleft=[controls.PointEditor(dialog_form=SimpleNameDialogForm())],
            attrs={'style': 'height: 600px;'},
        )
    )
