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


class FormMixin:
    def __init__(self, error_class=FormsetErrorList, renderer=None, **kwargs):
        kwargs['error_class'] = error_class
        if renderer is None:
            if self.default_renderer is None:
                renderer = FormRenderer()
            else:
                renderer = self.default_renderer
        if isinstance(renderer, type):
            renderer = renderer()
        kwargs['renderer'] = renderer
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
        if self.name and self.auto_id and '%s' in str(self.auto_id):
            return self.auto_id % self.name

    @cached_property
    def name(self):
        if name := getattr(self, '_name', None):
            parent_collection = getattr(self, 'parent_collection', None)
            if parent_collection and parent_collection.name:
                return f'{parent_collection.name}.{name}'
            else:
                return name

    def get_context(self):
        return {
            'form': self,
        }

    def get_field(self, field_name):
        return self.declared_fields[field_name]
