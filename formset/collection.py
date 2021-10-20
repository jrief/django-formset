from django.forms.forms import BaseForm
from django.forms.widgets import MediaDefiningClass
from django.forms.utils import ErrorDict, ErrorList, RenderableMixin
from django.utils.datastructures import MultiValueDict
from django.utils.functional import cached_property

from formset.exceptions import FormCollectionError
from formset.renderers.default import FormRenderer
from formset.utils import FormMixin, FormsetErrorList


class FormCollectionMeta(MediaDefiningClass):
    """
    Collect Forms declared on the base classes.
    """
    def __new__(cls, name, bases, attrs):
        # Collect forms and sub-collections from current class and remove them from attrs.
        attrs['declared_holders'] = {}
        for key, value in list(attrs.items()):
            if isinstance(value, (BaseForm, BaseFormCollection)):
                attrs.pop(key)
                setattr(value, '_name', key)
                if isinstance(value, BaseForm) and not isinstance(value, FormMixin):
                    value.__class__ = type(value.__class__.__name__, (FormMixin, value.__class__), {})
                attrs['declared_holders'][key] = value

        new_class = super().__new__(cls, name, bases, attrs)

        # Walk through the MRO.
        declared_holders = {}
        for base in reversed(new_class.__mro__):
            # Collect Form and FormCollection instances from base classes.
            if hasattr(base, 'declared_holders'):
                declared_holders.update(base.declared_holders)

            # Form shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_holders:
                    declared_holders.pop(attr)

        new_class.declared_holders = declared_holders

        return new_class


class BaseFormCollection(RenderableMixin):
    """
    The main implementation of all the FormCollection logic.
    """
    default_renderer = FormRenderer
    prefix = None
    template_name = 'formset/default/collection.html'

    def __init__(self, data=None, initial=None, renderer=None, prefix=None):
        self.data = MultiValueDict() if data is None else data
        self.initial = initial
        if prefix is not None:
            self.prefix = prefix
        self._errors = None  # Stores the errors after clean() has been called.

        # Initialize form renderer. Use a global default if not specified
        # either as an argument or as self.default_renderer.
        if renderer is None:
            renderer = self.default_renderer
            if isinstance(self.default_renderer, type):
                renderer = renderer()
        self.renderer = renderer

    def iter_single(self):
        for name, declared_holder in self.declared_holders.items():
            prefix = f'{self.prefix}.{name}' if self.prefix else name
            initial = None
            if isinstance(self.initial, dict):
                initial = self.initial.get(name)
            if initial is None:
                initial = declared_holder.initial
            holder = declared_holder.__class__(initial=initial, prefix=prefix, renderer=self.renderer)
            yield holder

    def iter_many(self):
        num_instances = 2
        if self.initial:
            if not isinstance(self.initial, list):
                errmsg = "{class_name} is declared to have siblings, but provided argument `{argument}` is not a list"
                raise FormCollectionError(errmsg.format(class_name=self.__class__.__name__, argument='initial'))
            num_instances = max(num_instances, len(self.initial))
        first, last = 0, len(self.declared_holders.items()) - 1
        # add initialized collections/forms
        for counter in range(num_instances):
            for item_num, (name, declared_holder) in enumerate(self.declared_holders.items()):
                prefix = f'{self.prefix}.{counter}.{name}' if self.prefix else f'{counter}.{name}'
                initial = None
                if self.initial and counter < len(self.initial):
                    initial = self.initial[counter].get(name)
                if initial is None:
                    initial = declared_holder.initial
                holder = declared_holder.__class__(initial=initial, prefix=prefix, renderer=self.renderer)
                holder.counter = counter
                if item_num == first:
                    holder.is_first = True
                if item_num == last:
                    holder.is_last = True
                yield holder
        # add empty placeholder as template for extra collections
        for item_num, (name, declared_holder) in enumerate(self.declared_holders.items()):
            prefix = f'{self.prefix}.${{counter}}.{name}' if self.prefix else f'${{counter}}.{name}'
            holder = declared_holder.__class__(prefix=prefix, renderer=self.renderer)
            holder.is_template = True
            holder.counter = '${counter}'
            if item_num == first:
                holder.is_first = True
            if item_num == last:
                holder.is_last = True
            yield holder

    def __iter__(self):
        if self.has_many:
            yield from self.iter_many()
        else:
            yield from self.iter_single()

    def get_context(self):
        return {
            'collection': self,
        }

    @property
    def errors(self):
        """Return an ErrorDict for the data provided for this form collection."""
        if self._errors is None:
            self.full_clean()
        return self._errors

    def is_valid(self):
        """Return True if all forms in this collection are valid."""
        return not self.errors

    def full_clean(self):
        if self.has_many:
            self.cleaned_data = []
            self._errors = ErrorList()
            for index, data in enumerate(self.data):
                self.cleaned_data.append({})
                for name, declared_holder in self.declared_holders.items():
                    holder = declared_holder.__class__(data=data.get(name))
                    if holder.is_valid():
                        self.cleaned_data[-1][name] = holder.cleaned_data
                    else:
                        self._errors.extend([{}] * (index - len(self._errors)))
                        self._errors.append({name: holder.errors.data})
        else:
            self.cleaned_data = {}
            self._errors = ErrorDict()
            for name, declared_holder in self.declared_holders.items():
                holder = declared_holder.__class__(data=self.data.get(name))
                if holder.is_valid():
                    self.cleaned_data[name] = holder.cleaned_data
                else:
                    self._errors.update({name: holder.errors.data})

    def clean(self):
        return self.cleaned_data

    @cached_property
    def has_many(self):
        """
        Returns True if current FormCollection manages a list of sibling forms.
        """
        return getattr(self, 'min_siblings', 0) > 0


class FormCollection(BaseFormCollection, metaclass=FormCollectionMeta):
    """
    Base class for a collection of forms. Attributes of this class which inherit from
    `django.forms.forms.BaseForm` are managed by this class.
    """
    def get_field(self, path):
        path = path.split('.', 1)
        key, path = path
        return self.holders[key].get_field(path)
