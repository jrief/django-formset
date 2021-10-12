import copy

from django.forms.forms import BaseForm
from django.forms.widgets import MediaDefiningClass
from django.forms.utils import ErrorDict, RenderableMixin
from django.utils.datastructures import MultiValueDict

from formset.renderers.default import FormRenderer
from formset.utils import FormMixin, FormsetErrorList


class FormCollectionMeta(MediaDefiningClass):
    """
    Collect Forms declared on the base classes.
    """
    def __new__(cls, name, bases, attrs):
        # Collect forms from current class and remove them from attrs.
        attrs['declared_forms'] = {}
        default_renderer = FormRenderer
        for base in bases:
            if hasattr(base, 'default_renderer'):
                default_renderer = base.default_renderer
                break
        if isinstance(default_renderer, type):
            default_renderer = default_renderer()
        for key, value in list(attrs.items()):
            if isinstance(value, BaseForm):
                attrs.pop(key)
                setattr(value, 'name', key)
                if not isinstance(value, FormMixin):
                    value.__class__ = type(value.__class__.__name__, (FormMixin, value.__class__), {})
                    value.renderer = default_renderer
                    value.error_class = FormsetErrorList
                attrs['declared_forms'][key] = value

        new_class = super().__new__(cls, name, bases, attrs)

        # Walk through the MRO.
        declared_forms = {}
        for base in reversed(new_class.__mro__):
            # Collect Forms from base class.
            if hasattr(base, 'declared_forms'):
                declared_forms.update(base.declared_forms)

            # Form shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_forms:
                    declared_forms.pop(attr)

        new_class.declared_forms = declared_forms

        return new_class


class BaseFormCollection(RenderableMixin):
    """
    The main implementation of all the FormCollection logic.
    """
    default_renderer = FormRenderer

    template_name = 'formset/default/form_collection.html'

    def __init__(self, data=None, renderer=None):
        self.data = MultiValueDict() if data is None else data
        self._errors = None  # Stores the errors after clean() has been called.

        # The declared_forms class attribute is the *class-wide* definition of
        # forms. Because a particular *instance* of the class might want to
        # alter self.forms, we create self.forms here by copying declared_forms.
        # Instances should always modify self.forms; they should not modify
        # self.declared_forms.
        self.forms = copy.deepcopy(self.declared_forms)

        # Initialize form renderer. Use a global default if not specified
        # either as an argument or as self.default_renderer.
        if renderer is None:
            renderer = self.default_renderer
            if isinstance(self.default_renderer, type):
                renderer = renderer()
        self.renderer = renderer

    def __iter__(self):
        for form in self.forms.values():
            yield form

    def get_context(self):
        return {
            'form_collection': self,
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
        self._errors = ErrorDict()
        self.cleaned_data = {}
        for name, form in self.forms.items():
            form = form.__class__(data=self.data.get(name))
            if form.is_valid():
                self.cleaned_data[name] = form.cleaned_data
            else:
                self._errors.update({name: form.errors.data})

    def clean(self):
        return self.cleaned_data


class FormCollection(BaseFormCollection, metaclass=FormCollectionMeta):
    """
    Base class for a collection of forms. Attributes of this class which inherit from
    `django.forms.forms.BaseForm` are managed by this class.
    """
    def get_field(self, form_name, field_name):
        return self.declared_forms[form_name].declared_fields[field_name]
