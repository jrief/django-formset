from django.forms import fields, widgets
from django.utils.translation import gettext_lazy as _

from formset.dialog import DialogForm
from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.widgets import Button, UploadedFileInput


class RichtextDialogForm(DialogForm):
    extension = None
    plugin_type = None
    is_transient = True
    induce_close = 'dismiss:active || revert:active || apply:active'
    template_name = 'formset/richtext/form_dialog.html'

    dismiss = Activator(
        label=_("Close"),
        widget=Button(
            action='dismiss',
        ),
    )
    revert = Activator(
        label=_("Revert"),
        widget=Button(
            action='revert',
            button_variant=ButtonVariant.DANGER,
        ),
    )
    apply = Activator(
        label=_("Apply"),
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
    icon = 'formset/icons/link.svg'
    prefix = 'simple_link_dialog'

    text = fields.CharField(
        label=_("Link Text"),
        widget=widgets.TextInput(attrs={
            'richtext-selection': True,
            'size': 50,
        })
    )
    url = fields.URLField(
        label=_("URL"),
        widget=widgets.URLInput(attrs={
            'size': 50,
            'richtext-mapping': 'href',
        }),
    )


class SimpleImageDialogForm(RichtextDialogForm):
    title = _("Edit Image")
    extension = 'simple_image'
    plugin_type = 'node'
    icon = 'formset/icons/image.svg'
    prefix = 'image_dialog'

    image = fields.ImageField(
        label=_("Uploaded Image"),
        widget=UploadedFileInput(attrs={
            'richtext-dataset': 'fileupload',
            'richtext-mapping': '{src: JSON.parse(element.dataset.fileupload).download_url}',
        }),
    )


class PlaceholderDialogForm(RichtextDialogForm):
    title = _("Edit Placeholder")
    extension = 'procurator'  # The named extension 'placeholder' is already declared by TipTap
    plugin_type = 'mark'
    icon = 'formset/icons/placeholder.svg'
    prefix = 'placeholder_dialog'
    variable_pattern = r'^[A-Za-z_][0-9A-Za-z_\.]{0,254}$'

    variable_name = fields.RegexField(
        regex=variable_pattern,
        label=_("Variable Name"),
        widget=widgets.TextInput(attrs={
            'richtext-mapping': True,
            'size': 50,
            'pattern': variable_pattern,
        }),
    )
    sample_value = fields.CharField(
        label=_("Sample Value"),
        widget=widgets.TextInput(attrs={
            'richtext-selection': True,
            'size': 50,
        })
    )
