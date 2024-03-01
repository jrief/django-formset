from django.forms import forms

from formset.utils import FormMixin


class DialogDeclarativeFieldsMetaclass(forms.DeclarativeFieldsMetaclass):
    def __new__(mcs, name, bases, attrs):
        return super().__new__(mcs, name, bases, attrs)


class DialogForm(FormMixin, forms.BaseForm, metaclass=DialogDeclarativeFieldsMetaclass):
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
        # context['form'].extension_file = f'formset/tiptap/extensions/{self.extension}.js' if self.extension else None
        return context
