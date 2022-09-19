import copy

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorDict, ErrorList
from django.utils.functional import cached_property

from formset.boundfield import BoundField
from formset.renderers.default import FormRenderer

MARKED_FOR_REMOVAL = '_marked_for_removal_'


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
    ignore_marked_for_removal = getattr(settings, 'FORMSET_IGNORE_MARKED_FOR_REMOVAL', False)

    def __init__(self, **kwargs):
        self.marked_for_removal = False
        super().__init__(**kwargs)

    def replicate(self, data=None, initial=None, prefix=None, renderer=None, ignore_marked_for_removal=None):
        replica = copy.copy(self)
        if hasattr(self, 'declared_holders'):
            replica.declared_holders = {
                key: holder.replicate(
                    renderer=renderer,
                    ignore_marked_for_removal=ignore_marked_for_removal,
                ) for key, holder in self.declared_holders.items()
            }
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
        if ignore_marked_for_removal is not None:
            replica.ignore_marked_for_removal = ignore_marked_for_removal
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

    def _clean_for_removal(self):
        """
        Forms which have been marked for removal, clean their received form data,
        but always keep them as validated.
        """
        self._errors = ErrorDict()
        self.cleaned_data = {}
        for name, bf in self._bound_items():
            field = bf.field
            value = bf.initial if field.disabled else bf.data
            try:
                value = field.clean(value)
                if hasattr(self, f'clean_{name}'):
                    self.cleaned_data[name] = value
                    value = getattr(self, f'clean_{name}')()
            except ValidationError:
                pass  # ignore all validation errors for removed forms
            finally:
                self.cleaned_data[name] = value
        self.cleaned_data[MARKED_FOR_REMOVAL] = True
        self.marked_for_removal = True

    def is_valid(self):
        if self.is_bound and MARKED_FOR_REMOVAL in self.data:
            self._clean_for_removal()
            return True
        return super().is_valid()


class FormDecoratorMixin:
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
        auto_id = self.auto_id if '%s' in str(self.auto_id) else 'id_%s'
        if self.prefix:
            return auto_id % self.prefix
        else:
            return auto_id % self.__class__.__name__.lower()


class FormMixin(FormDecoratorMixin, HolderMixin):
    """
    Mixin class to be added to a native Django Form. This is required to add
    """

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
        return self.fields[field_name]
