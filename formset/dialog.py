from django.forms import forms

from formset.utils import FormMixin


class DialogForm(FormMixin, forms.BaseForm, metaclass=forms.DeclarativeFieldsMetaclass):
    template_name = 'formset/default/form_dialog.html'
    induce_open, induce_close = None, None
    title = None

    def __init__(self, induce_open=None, induce_close=None, title=None, **kwargs):
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
