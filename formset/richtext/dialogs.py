from django.forms import fields, widgets
from django.utils.translation import gettext_lazy as _

from formset.dialog import DialogForm
from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.widgets import Button


class RichtextDialogForm(DialogForm):
    extension = None
    plugin_type = None
    is_transient = True
    induce_close = 'dismiss:active || revert:active || apply:active'
    template_name = 'formset/richtext/form_dialog.html'

    dismiss = Activator(
        label="Close",
        widget=Button(
            action='dismiss',
        ),
    )
    revert = Activator(
        label="Revert",
        widget=Button(
            action='revert',
            button_variant=ButtonVariant.DANGER,
        ),
    )
    apply = Activator(
        label="Apply",
        widget=Button(
            action='apply',
            button_variant=ButtonVariant.PRIMARY,
        ),
    )

    def get_context(self):
        context = super().get_context()
        context['extension_script'] = f'formset/tiptap-extensions/{self.extension}.tjs' if self.extension else None
        return context


class SimpleLinkDialogForm(RichtextDialogForm):
    title = _("Edit Link")
    extension = 'simple_link'
    plugin_type = 'mark'
    prefix = 'simple_link_dialog'

    text = fields.CharField(
        label="Text",
        widget=widgets.TextInput(attrs={
            'richtext-selection': True,
            'size': 50,
        })
    )
    url = fields.URLField(
        label="Link",
        widget=widgets.URLInput(attrs={
            'size': 50,
            'richtext-mapping': 'href',
        }),
    )
