from django.forms import forms

from formset.renderers import ButtonVariant
from formset.utils import FormMixin
from formset.widgets import Button


class DialogForm(FormMixin, forms.BaseForm, metaclass=forms.DeclarativeFieldsMetaclass):
    template_name = 'formset/default/form_dialog.html'
    is_modal = False
    induce_open, induce_close = None, None
    prologue, epilogue = None, None
    title = None

    def __init__(self, is_modal=False, induce_open=None, induce_close=None, title=None, **kwargs):
        if is_modal:
            self.is_modal = True
        if induce_open:
            self.induce_open = induce_open
        if induce_close:
            self.induce_close = induce_close
        if title:
            self.title = title
        super().__init__(**kwargs)

    def get_context(self):
        context = super().get_context()
        context['form'].method = 'dialog'
        return context


ApplyButton = Button(action='activate("apply")', button_variant=ButtonVariant.PRIMARY)
CancelButton = Button(action='activate("cancel")', button_variant=ButtonVariant.SECONDARY)
RevertButton = Button(action='activate("revert")', button_variant=ButtonVariant.DANGER)
