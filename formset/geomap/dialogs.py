from django.forms import fields

from formset.dialog import ActionDialogForm


class GeoMapDialogForm(ActionDialogForm):
    extension = None
    template_name = 'formset/default/form_dialog.html'


class SimpleNameDialogForm(GeoMapDialogForm):
    extension = 'simple_name'

    name = fields.CharField()
