from django.core.exceptions import ImproperlyConfigured
from django.forms import forms

from formset.utils import FormMixin


class DialogForm(FormMixin, forms.Form):
    template_name = 'formset/default/form_dialog.html'
    open_condition = None
    title = None

    def __init__(self, open_condition=None, title=None, **kwargs):
        if open_condition:
            self.open_condition = open_condition
        if not self.open_condition:
            raise ImproperlyConfigured("FormDialog requires an `open_condition`.")
        if title:
            self.title = title
        super().__init__(**kwargs)

    def get_context(self):
        context = super().get_context()
        context['form'].method = 'dialog'
        context.update(
            open_condition=self.open_condition,
            title=self.title,
        )
        return context
