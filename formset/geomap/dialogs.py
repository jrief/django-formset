from django.forms import fields
from django.utils.translation import gettext_lazy as _

from formset.dialog import ActionDialogForm, ApplyButton, CancelButton
from formset.formfields.activator import Activator


class GeoMapDialogForm(ActionDialogForm):
    extension = None
    template_name = 'formset/default/form_dialog.html'

    cancel = Activator(
        label=_("Cancel"),
        widget=CancelButton,
    )
    apply = Activator(
        label=_("Apply"),
        widget=ApplyButton,
        initial='apply',
    )


class SimpleNameDialogForm(GeoMapDialogForm):
    title = _("Edit Marker Name")
    extension = 'simple_name'

    name = fields.CharField()
