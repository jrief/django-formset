from django.core.exceptions import ImproperlyConfigured
from django.forms import forms

from formset.utils import FormMixin


class DialogForm(FormMixin, forms.Form):
    template_name = 'formset/default/form_dialog.html'
    induce_open, induce_close, induce_save = None, None, None
    title = None

    def __init__(self, induce_open=None, induce_close=None, induce_save=None, title=None, **kwargs):
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
        context.update(
            induce_open=self.induce_open,
            induce_close=self.induce_close,
            title=self.title,
        )
        return context
