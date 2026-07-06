from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm

from formset.forms import DeclarativeFieldsetMetaclass, FormMixin, FormsetModelFormMetaclass
from formset.renderers import ButtonVariant
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


class DialogForm(DialogFormMixin, BaseForm, metaclass=DeclarativeFieldsetMetaclass):
    template_name = 'formset/default/form_dialog.html'


class DialogModelForm(DialogFormMixin, BaseModelForm, metaclass=FormsetModelFormMetaclass):
    template_name = 'formset/default/form_dialog.html'


ApplyButton = Button(action='activate("apply")', button_variant=ButtonVariant.PRIMARY)
CancelButton = Button(action='activate("close")', button_variant=ButtonVariant.SECONDARY)
RevertButton = Button(action='activate("revert")', button_variant=ButtonVariant.DANGER)


class ActionDialogForm(DialogForm):
    is_transient = True
    _prefix = '.dialog_'

    @property
    def prefix(self):
        return f'{self._prefix}{self.extension}'

    @prefix.setter
    def prefix(self, value):
        if self._prefix.startswith('.'):
            self._prefix = f'{value}{self._prefix}'

    @property
    def induce_open(self):
        return f'.dialog_{self.extension}:active'

    @property
    def induce_close(self):
        return f'.dialog_{self.extension}.cancel:active || .dialog_{self.extension}.revert:active || .dialog_{self.extension}.apply:active'
