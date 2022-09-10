from django.core.exceptions import ImproperlyConfigured
from django.forms import forms

from formset.utils import FormMixin


class FieldsetMixin(FormMixin):
    show_if = None
    hide_if = None
    disable_if = None
    legend = None
    help_text = None
    template_name = 'formset/default/fieldset.html'

    def __init__(self, **kwargs):
        show_if = kwargs.pop('show_if', None)
        hide_if = kwargs.pop('hide_if', None)
        if show_if and hide_if:
            raise ImproperlyConfigured(f"class {self.__class__} can accept either `show_if` or `hide_if`, but not both.")
        if show_if:
            self.show_if = show_if
        elif hide_if:
            self.hide_if = hide_if
        if disable_if := kwargs.pop('disable_if', None):
            self.disable_if = disable_if
        if legend := kwargs.pop('legend', None):
            self.legend = legend
        if help_text := kwargs.pop('help_text', None):
            self.help_text = help_text
        super().__init__(**kwargs)

    def get_context(self):
        context = super().get_context()
        context.update(
            form_id=self.form_id,
            show_if=self.show_if,
            hide_if=self.hide_if,
            disable_if=self.disable_if,
            legend=self.legend,
            help_text=self.help_text,
        )
        return context


class Fieldset(FieldsetMixin, forms.Form):
    """
    This is just DOM sugar wrapped into a Form. It therefore behaves like a Form object and should
    be used as such. Its purpose is to add visual elements to a `<form>`. Remember, a Form is just a
    data-abstraction layer, has no display properties and is not intended to be styled or anotated.
    On the other side, a <fieldset> may offer a `<legend>`, a border and the possibility to
    show/hide or disable a set of fields. A `HTMLFieldSetElement` however does not has any field
    validation functionality, this is left to the `HTMLFormElement`.
    """
    def __repr__(self):
        return f'<{self.__class__.__name__} legend="{self.legend}" template_name="{self.template_name}">'
