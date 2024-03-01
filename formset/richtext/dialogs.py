from django.forms import forms

from formset.utils import FormDecoratorMixin


class DialogForm(FormDecoratorMixin, forms.Form):
    template_name = 'formset/default/dialog_form.html'

    def __init__(self, **kwargs):
        kwargs.setdefault('auto_id', 'id_dialog_%s')
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<{self.__class__.__name__} template_name="{self.template_name}">'
