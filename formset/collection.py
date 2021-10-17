from django.forms.forms import BaseForm
from django.forms.widgets import MediaDefiningClass
from django.forms.utils import ErrorDict, ErrorList, RenderableMixin
from django.utils.datastructures import MultiValueDict

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
        if self.has_many:
            self.holders = self.instantiate_many_holders()
        else:
            self.holders = self.instantiate_holders()

        # Initialize form renderer. Use a global default if not specified
        # either as an argument or as self.default_renderer.
        if renderer is None:
            renderer = self.default_renderer
            if isinstance(self.default_renderer, type):
                renderer = renderer()
        self.set_form_renderer(renderer)

    def __iter__(self):
        for holder in self.holders:
            yield holder

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
                        self.cleaned_data[-1]['name'] = holder.cleaned_data
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

    @property
    def has_many(self):
        """
        Returns True if current FormCollection manages a list of sibling forms.
        """
        return getattr(self, 'min_siblings', 0) > 0

    def set_form_renderer(self, renderer):
        self.renderer = renderer
        for holder in self.holders:
            if isinstance(holder, BaseFormCollection):
                holder.set_form_renderer(renderer)
            elif isinstance(holder, BaseForm):
                holder.renderer = renderer
                holder.error_class = FormsetErrorList
            else:
                raise RuntimeError("Should never reach this line")  # noqa

    def instantiate_holders(self):
        """
        # The declared_holders class attribute is the *class-wide* definition of
        # collections and/or forms. Because a particular *instance* of the class might
        # want to alter self.holders, we create it here by instantiating each entity of
        # declared_holder again.
        """
        instantiated_holders = []
        for name, declared_holder in self.declared_holders.items():
            prefix = f'{self.prefix}.{name}' if self.prefix else name
            data = self.data.get(name)
            initial = self.initial.get(name) if self.initial else None
            if initial is None:
                initial = declared_holder.initial
            holder = declared_holder.__class__(data=data, initial=initial, prefix=prefix)
            instantiated_holders.append(holder)
        return instantiated_holders

    def instantiate_many_holders(self):
        instantiated_holders = []
        num_instances = 2
        errmsg = "{class_name} is declared to have siblings, but provided argument `{argument}` is not a list"
        if self.data:
            if not isinstance(self.data, list):
                raise FormCollectionError(errmsg.format(class_name=self.__class__.__name__, argument='data'))
            num_instances = max(num_instances, len(self.data))
        if self.initial is not None:
            if not isinstance(self.initial, list):
                raise FormCollectionError(errmsg.format(class_name=self.__class__.__name__, argument='initial'))
            num_instances = max(num_instances, len(self.initial))
        for index in range(num_instances):
            for name, declared_holder in self.declared_holders.items():
                prefix = f'{self.prefix}.{index}.{name}' if self.prefix else f'{index}.{name}'
                try:
                    data = self.data[index][name]
                except (IndexError, KeyError, TypeError):
                    data = None
                try:
                    initial = self.initial[index][name]
                except (IndexError, KeyError, TypeError):
                    try:
                        initial = declared_holder.initial[index]
                    except (IndexError, KeyError):
                        initial = None
                holder = declared_holder.__class__(data=data, initial=initial, prefix=prefix)
                instantiated_holders.append(holder)
        return instantiated_holders


class FormCollection(BaseFormCollection, metaclass=FormCollectionMeta):
    """
    Base class for a collection of forms. Attributes of this class which inherit from
    `django.forms.forms.BaseForm` are managed by this class.
    """
    def get_field(self, path):
        path = path.split('.', 1)
        key, path = path
        return self.holders[key].get_field(path)
