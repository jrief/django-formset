from django.forms import forms
from django.forms.fields import CharField, ImageField, URLField
from django.forms.widgets import URLInput
from django.utils.translation import gettext_lazy as _

from formset.utils import FormDecoratorMixin
from formset.widgets import UploadedFileInput


class DialogForm(FormDecoratorMixin, forms.Form):
    template_name = 'formset/default/dialog_form.html'

    def __init__(self, **kwargs):
        kwargs.setdefault('auto_id', 'id_dialog_%s')
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<{self.__class__.__name__} template_name="{self.template_name}">'


class LinkFormDialog(DialogForm):
    modal_title = _("Edit Link")
    method = 'dialog'
    prefix = 'edit_link'

    text = CharField(
        label=_("Text"),
    )

    url = URLField(
        label=_("Link"),
        widget=URLInput(attrs={'size': 50}),
    )


class ImageFormDialog(DialogForm):
    modal_title = _("Edit Image")
    method = 'dialog'
    prefix = "edit_image"

    image = ImageField(
        label=_("Image"),
        widget=UploadedFileInput(),
    )
