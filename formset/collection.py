from django.core.exceptions import NON_FIELD_ERRORS
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm, construct_instance, model_to_dict
from django.forms.utils import ErrorDict, ErrorList, RenderableMixin
from django.forms.widgets import MediaDefiningClass
from django.utils.datastructures import MultiValueDict

from formset.exceptions import FormCollectionError
from formset.renderers.default import FormRenderer
from formset.utils import MARKED_FOR_REMOVAL, FormMixin, FormsetErrorList, HolderMixin

COLLECTION_ERRORS = '_collection_errors_'


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
                    value.error_class = FormsetErrorList
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


class BaseFormCollection(HolderMixin, RenderableMixin):
    """
    The main implementation of all the FormCollection logic.
    """
    default_renderer = None
    prefix = None
    template_name = 'formset/default/collection.html'
    min_siblings = None
    max_siblings = None
    extra_siblings = None
    is_sortable = None
    legend = None
    help_text = None
    add_label = None
    ignore_marked_for_removal = None

    def __init__(self, data=None, initial=None, renderer=None, prefix=None, min_siblings=None,
                 max_siblings=None, extra_siblings=None, is_sortable=None, legend=None, help_text=None):
        self.data = MultiValueDict() if data is None else data
        self.initial = initial
        if prefix is not None:
            self.prefix = prefix
        self._errors = None  # Stores the errors after `clean()` has been called.
        if min_siblings is not None:
            self.min_siblings = min_siblings
        if max_siblings is not None:
            self.max_siblings = max_siblings
        if extra_siblings is not None:
            self.extra_siblings = extra_siblings
        if self.has_many:
            if self.min_siblings is None:
                self.min_siblings = 1
            if self.extra_siblings is None:
                self.extra_siblings = 0
            if is_sortable is not None:
                self.is_sortable = is_sortable
        else:
            self.is_sortable = False
        if legend is not None:
            self.legend = legend
        if help_text is not None:
            self.help_text = help_text

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
            holder = declared_holder.replicate(
                initial=initial,
                prefix=prefix,
                renderer=self.renderer,
                ignore_marked_for_removal=self.ignore_marked_for_removal,
            )
            holder.is_single = True
            yield holder

    def iter_many(self):
        num_siblings = max(self.min_siblings, self.extra_siblings)
        if self.initial:
            if not isinstance(self.initial, list):
                errmsg = "{class_name} is declared to have siblings, but provided argument `{argument}` is not a list"
                raise FormCollectionError(errmsg.format(class_name=self.__class__.__name__, argument='initial'))
            num_siblings = max(num_siblings, len(self.initial)) + self.extra_siblings
            if self.max_siblings is not None:
                num_siblings = min(self.max_siblings, num_siblings)

        first, last = 0, len(self.declared_holders.items()) - 1
        # add initialized collections/forms
        for position in range(num_siblings):
            for item_num, (name, declared_holder) in enumerate(self.declared_holders.items()):
                prefix = f'{self.prefix}.{position}.{name}' if self.prefix else f'{position}.{name}'
                initial = None
                if self.initial and position < len(self.initial):
                    initial = self.initial[position].get(name)
                if initial is None:
                    initial = declared_holder.initial
                holder = declared_holder.replicate(
                    initial=initial,
                    prefix=prefix,
                    renderer=self.renderer,
                    ignore_marked_for_removal=self.ignore_marked_for_removal,
                )
                holder.position = position
                if item_num == first:
                    holder.is_first = True
                if item_num == last:
                    holder.is_last = True
                yield holder
        # add empty placeholder as template for extra collections
        for item_num, (name, declared_holder) in enumerate(self.declared_holders.items()):
            if self.prefix:
                count = self.prefix.count('${position')
                assert count < 10, "Maximum number of nested FormCollections reached"
                # this context rewriting is necessary to render nested templates properly
                position = f'${{position_{count}}}' if count > 0 else '${position}'
                prefix = f'{self.prefix}.{position}.{name}'
            else:
                position = '${position}'
                prefix = f'${{position}}.{name}'
            holder = declared_holder.replicate(
                prefix=prefix,
                renderer=self.renderer,
                ignore_marked_for_removal=self.ignore_marked_for_removal,
            )
            holder.is_template = True
            holder.position = position
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
                cleaned_data = {}
                for name, declared_holder in self.declared_holders.items():
                    if name in data:
                        holder = declared_holder.replicate(
                            data=data[name],
                            ignore_marked_for_removal=self.ignore_marked_for_removal,
                        )
                        if holder.ignore_marked_for_removal and MARKED_FOR_REMOVAL in holder.data:
                            break
                        if holder.is_valid():
                            cleaned_data[name] = holder.cleaned_data
                        else:
                            self._errors.extend([{}] * (index - len(self._errors)))
                            self._errors.append({name: holder.errors})
                    else:
                        # can only happen, if client bypasses browser control
                        self._errors.extend([{}] * (index - len(self._errors)))
                        self._errors.append({name: {NON_FIELD_ERRORS: ["Form data is missing."]}})
                else:
                    self.cleaned_data.append(cleaned_data)
            if len(self.cleaned_data) < self.min_siblings:
                # can only happen, if client bypasses browser control
                self._errors.clear()
                self._errors.append({COLLECTION_ERRORS: ["Too few siblings."]})
            if self.max_siblings and len(self.cleaned_data) > self.max_siblings:
                # can only happen, if client bypasses browser control
                self._errors.clear()
                self._errors.append({COLLECTION_ERRORS: ["Too many siblings."]})
        else:
            self.cleaned_data = {}
            self._errors = ErrorDict()
            for name, declared_holder in self.declared_holders.items():
                if name in self.data:
                    holder = declared_holder.replicate(
                        data=self.data[name],
                        ignore_marked_for_removal=self.ignore_marked_for_removal,
                    )
                    if holder.is_valid():
                        self.cleaned_data[name] = holder.cleaned_data
                    else:
                        self._errors.update({name: holder.errors})
                else:
                    # can only happen, if client bypasses browser control
                    self._errors.update({name: {NON_FIELD_ERRORS: ["Form data is missing."]}})

    def clean(self):
        return self.cleaned_data

    @property
    def has_many(self):
        """
        Returns True if current FormCollection manages a list of sibling forms/(sub-)collections.
        """
        return not (self.min_siblings is None and self.max_siblings is None and self.extra_siblings is None)

    def render(self, template_name=None, context=None, renderer=None):
        if not (renderer or self.renderer):
            renderer = FormRenderer()
        return super().render(template_name, context, renderer)

    def model_to_dict(self, main_object):
        """
        Create initial data from a main object. This then is used to fill the initial data from all its child
        collections and forms.
        Forms which do not correspond to the model given by the main object, are themselves responsible to
        access the proper referenced models.
        """
        object_data = {}
        for name, holder in self.declared_holders.items():
            if callable(getattr(holder, 'model_to_dict', None)):
                object_data[name] = holder.model_to_dict(main_object)
            elif isinstance(holder, BaseModelForm):
                opts = holder._meta
                object_data[name] = model_to_dict(main_object, opts.fields, opts.exclude)
            else:
                object_data[name] = model_to_dict(main_object)
        return object_data

    def construct_instance(self, main_object, cleaned_data):
        """
        Construct the main object and its related objects from the nested dictionary of cleaned data.
        Forms which do not correspond to the model given by the main object, are responsible themselves
        to store the corresponding data inside their related models.
        """
        for name, holder in self.declared_holders.items():
            if callable(getattr(holder, 'construct_instance', None)):
                holder.construct_instance(main_object, self.cleaned_data[name])
            elif isinstance(holder, BaseModelForm):
                opts = holder._meta
                holder.cleaned_data = self.cleaned_data[name]
                holder.instance = main_object
                construct_instance(holder, main_object, opts.fields, opts.exclude)
                holder.save()

    __str__ = render
    __html__ = render


class FormCollection(BaseFormCollection, metaclass=FormCollectionMeta):
    """
    Base class for a collection of forms. Attributes of this class which inherit from
    `django.forms.forms.BaseForm` are managed by this class.
    """
    def get_field(self, field_path):
        path = field_path.split('.', 1)
        key, path = path
        return self.declared_holders[key].get_field(path)
