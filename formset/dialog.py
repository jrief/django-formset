from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass
from django.forms.models import BaseModelForm, ModelFormMetaclass

from formset.renderers import ButtonVariant
from formset.utils import FormMixin
from formset.widgets import Button


class DialogFormMixin(FormMixin):
    title = None
    is_modal = False
    induce_open, induce_close = None, None
    prologue, epilogue = None, None

    def __init__(self, title=None, is_modal=False, induce_open=None, induce_close=None, **kwargs):
        if title:
            self.title = title
        if is_modal:
            self.is_modal = True
        if induce_open:
            self.induce_open = induce_open
        if induce_close:
            self.induce_close = induce_close
        super().__init__(**kwargs)

    def get_context(self):
        context = super().get_context()
        context['form'].method = 'dialog'
        return context


class DialogForm(DialogFormMixin, BaseForm, metaclass=DeclarativeFieldsMetaclass):
    template_name = 'formset/default/form_dialog.html'


class DialogModelForm(DialogFormMixin, BaseModelForm, metaclass=ModelFormMetaclass):
    template_name = 'formset/default/form_dialog.html'


ApplyButton = Button(action='activate("apply")', button_variant=ButtonVariant.PRIMARY)
CancelButton = Button(action='activate("close")', button_variant=ButtonVariant.SECONDARY)
RevertButton = Button(action='activate("revert")', button_variant=ButtonVariant.DANGER)
