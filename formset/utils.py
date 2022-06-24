import copy

from django.forms.utils import ErrorList
from django.utils.functional import cached_property

from formset.boundfield import BoundField
from formset.renderers.default import FormRenderer


class FormsetErrorList(ErrorList):
    template_name = 'formset/default/field_errors.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if args and hasattr(args[0], 'client_messages'):
            self.client_messages = args[0].client_messages

    def copy(self):
        copy = super().copy()
        if hasattr(self, 'client_messages'):
            copy.client_messages = self.client_messages
        return copy

    def get_context(self):
        return {
            'errors': self,
            'client_messages': self.client_messages,
        }


class HolderMixin:
    def replicate(self, data=None, initial=None, prefix=None, renderer=None):
        replica = copy.copy(self)
        replica.data = data
        replica.is_bound = data is not None
        replica._errors = None
        try:
            delattr(replica, 'cleaned_data')
        except AttributeError:
            pass
        if hasattr(replica, 'files'):
            replica.files.clear()
        if initial:
            replica.initial = initial
        if prefix:
            replica.prefix = prefix
        if isinstance(replica.renderer, FormRenderer):
            return replica
        if self.default_renderer:
            if isinstance(self.default_renderer, type):
                replica.renderer = self.default_renderer()
            else:
                replica.renderer = self.default_renderer
        elif renderer:
            replica.renderer = renderer
        else:
            replica.renderer = FormRenderer()
        return replica


class FormMixin(HolderMixin):
    """
    Mixin class to be added to a native Django Form. This is required to add
    """

    def __init__(self, error_class=FormsetErrorList, **kwargs):
        kwargs['error_class'] = error_class
        super().__init__(**kwargs)

    def __getitem__(self, name):
        "Returns a modified BoundField for the given field."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError(f"Key {name} not found in Form")
        return BoundField(self, field, name)

    @cached_property
    def form_id(self):
        # The "form" tag is used to link fields to their form owner
        # See https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input#attr-form for details
        if self.prefix and self.auto_id and '%s' in str(self.auto_id):
            return self.auto_id % self.prefix

    def add_prefix(self, field_name):
        """
        Return the field name with a prefix preended, if this Form has a prefix set.
        """
        return f'{self.prefix}.{field_name}' if self.prefix else field_name

    def get_context(self):
        """
        This simplified method just returns the ``form``, but not the ``fields``, ``hidden_fields``
        and ``errors``, since they are rendered by the included ``form.html`` template.
        """
        return {
            'form': self,
        }

    def get_field(self, field_name):
        return self.declared_fields[field_name]
