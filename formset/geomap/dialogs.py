from django.forms import fields, widgets
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from formset.dialog import ApplyButton, CancelButton, TransientDialogForm
from formset.formfields.activator import Activator


class GeoMapDialogForm(TransientDialogForm):
    template_name = 'formset/geomap/form_dialog.html'
    icon = 'formset/geomap/icons/edit-marker.svg'

    cancel = Activator(
        label=_("Cancel"),
        widget=CancelButton,
    )
    apply = Activator(
        label=_("Apply"),
        widget=ApplyButton,
        initial='apply',
    )

    def __init__(self, extension=None, icon=None, *args, **kwargs):
        if extension:
            self.extension = extension
        if icon:
            self.icon = icon
        super().__init__(*args, **kwargs)

    @property
    def induce_close(self):
        return f'.dialog_{self.extension}.cancel:active || .dialog_{self.extension}.apply:active'

    @cached_property
    def button_icon(self):
        if icon := getattr(self, 'icon', None):
            return icon
        return f'formset/geomap/icons/{self.extension.lower()}.svg'


class SimpleNameDialogForm(GeoMapDialogForm):
    title = _("Edit Marker Name")
    extension = 'simple_name'
    properties_map = {'name': 'name'}

    name = fields.CharField()


class LookupDialogForm(TransientDialogForm):
    title = _("Lookup by Address")
    extension = 'address_lookup'
    properties_map = {'addressLookupUrl': 'https://nominatim.openstreetmap.org/search'}
    template_name = 'formset/geomap/form_dialog.html'
    epilogue = mark_safe('<ul role="listbox"></ul>')  # here the results of the address lookup will be displayed

    lookup_address = fields.CharField(
        label=_("Address"),
        required=False,
        widget=widgets.SearchInput(
            attrs={'size': 60, 'placeholder': _("Address to look up")},
        ),
    )
    cancel = Activator(
        label=_("Cancel"),
        widget=CancelButton,
    )
    apply = Activator(
        label=_("Apply"),
        widget=ApplyButton,
        initial='apply',
    )

    @property
    def induce_open(self):
        return None

    @property
    def induce_close(self):
        return f'.dialog_{self.extension}.cancel:active || .dialog_{self.extension}.apply:active'
