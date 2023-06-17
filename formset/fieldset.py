from django.core.exceptions import ImproperlyConfigured
from django.forms import forms

from formset.utils import FormMixin


class FieldsetMixin(FormMixin):
    show_condition = None
    hide_condition = None
    disable_condition = None
    legend = None
    help_text = None
    template_name = 'formset/default/fieldset.html'

    def __init__(self, **kwargs):
        show_condition = kwargs.pop('show_condition', None)
        hide_condition = kwargs.pop('hide_condition', None)
        if show_condition and hide_condition:
            msg = f"class {self.__class__} can accept either `show_condition` or `hide_condition`, but not both."
            raise ImproperlyConfigured(msg)
        if show_condition:
            self.show_condition = show_condition
        elif hide_condition:
            self.hide_condition = hide_condition
        if disable_condition := kwargs.pop('disable_condition', None):
            self.disable_condition = disable_condition
        if legend := kwargs.pop('legend', None):
            self.legend = legend
        if help_text := kwargs.pop('help_text', None):
            self.help_text = help_text
        super().__init__(**kwargs)

    def get_context(self):
        context = super().get_context()
        context.update(
            form_id=self.form_id,
            show_condition=self.show_condition,
            hide_condition=self.hide_condition,
            disable_condition=self.disable_condition,
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
    show/hide or disable a set of fields. A `HTMLFieldSetElement` however does not have any field
    validation functionality, this is left to the `HTMLFormElement`.
    """
    def __repr__(self):
        return f'<{self.__class__.__name__} legend="{self.legend}" template_name="{self.template_name}">'
