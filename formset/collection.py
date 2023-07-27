import operator
from functools import reduce

from django.core import validators
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.utils import IntegrityError
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm, construct_instance, model_to_dict
from django.forms.utils import ErrorDict, ErrorList, RenderableMixin
from django.forms.widgets import MediaDefiningClass
from django.utils.datastructures import MultiValueDict
from django.utils.text import get_text_list
from django.utils.translation import gettext_lazy

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
    auto_id = 'id_%s'
    prefix = None
    template_name = 'formset/default/collection.html'
    instance = None
    min_siblings = None
    max_siblings = None
    extra_siblings = None
    is_sortable = None
    legend = None
    help_text = None
    add_label = None
    ignore_marked_for_removal = None
    empty_values = list(validators.EMPTY_VALUES)

    def __init__(self, data=None, initial=None, renderer=None, auto_id=None, prefix=None, instance=None,
                 min_siblings=None, max_siblings=None, extra_siblings=None, is_sortable=None, legend=None,
                 help_text=None):
        self.data = MultiValueDict() if data is None else data
        self.initial = initial
        if auto_id is not None:
            self.auto_id = auto_id
        if prefix is not None:
            self.prefix = prefix
        self._errors = None  # Stores the errors after `clean()` has been called.
        if instance:
            self.instance = instance
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
            self.fresh_and_empty = False
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
                auto_id=self.auto_id,
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
                    auto_id=self.auto_id,
                    prefix=prefix,
                    renderer=self.renderer,
                    ignore_marked_for_removal=self.ignore_marked_for_removal,
                )
                holder.position = position
                if item_num == first:
                    holder.is_first = True
                if item_num == last:
                    holder.is_last = True
                if initial in self.empty_values and (position >= self.min_siblings or self.fresh_and_empty):
                    holder.fresh_and_empty = True
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
        def is_valid(errors):
            if isinstance(errors, dict):
                return all(is_valid(e) for e in errors.values())
            if isinstance(errors, list):
                return all(is_valid(e) for e in errors)
            assert isinstance(errors, str)
            return False

        if self._errors is None:
            self.full_clean()
            self.validate_siblings_count()
        return is_valid(self._errors)


    def full_clean(self):
        if self.has_many:
            self.valid_holders = []
            self._errors = ErrorList()
            for data in self.data:
                if data is None:
                    continue
                instance = self.retrieve_instance(data)
                valid_holders = {}
                errors = ErrorDict()
                for name, declared_holder in self.declared_holders.items():
                    if name in data:
                        holder = declared_holder.replicate(
                            data=data[name],
                            instance=instance,
                            ignore_marked_for_removal=self.ignore_marked_for_removal,
                        )
                        if MARKED_FOR_REMOVAL in holder.data:
                            if holder.ignore_marked_for_removal:
                                break
                            if getattr(holder, 'has_many', False):
                                holder.marked_for_removal = True
                            elif self.has_many:
                                self.marked_for_removal = True
                        if holder.is_valid():
                            valid_holders[name] = holder
                        errors[name] = holder._errors
                    else:
                        # can only happen, if client bypasses browser control
                        errors[name] = {NON_FIELD_ERRORS: ["Form data is missing."]}
                else:
                    self.valid_holders.append(valid_holders)
                    self._errors.append(errors)
            self.validate_unique()
        else:
            self.valid_holders = {}
            self._errors = ErrorDict()
            for name, declared_holder in self.declared_holders.items():
                if name in self.data:
                    instance = self.retrieve_instance(self.data[name])
                    holder = declared_holder.replicate(
                        data=self.data[name],
                        instance=instance,
                        ignore_marked_for_removal=self.ignore_marked_for_removal,
                    )
                    if holder.is_valid():
                        self.valid_holders[name] = holder
                    self._errors[name] = holder._errors
                else:
                    # can only happen, if client bypasses browser control
                    self._errors[name] = {NON_FIELD_ERRORS: ["Form data is missing."]}

    def validate_unique(self):
        unique_fields = {self.related_field} if getattr(self, 'related_field', None) else set()
        all_unique_checks = set()
        for valid_holders in self.valid_holders:
            for name, holder in valid_holders.items():
                if isinstance(holder, BaseModelForm):
                    exclude = holder._get_validation_exclusions().difference(unique_fields)
                    unique_checks, date_checks = holder.instance._get_unique_checks(
                        exclude=exclude,
                        include_meta_constraints=True,
                    )
                    all_unique_checks.update(unique_checks)

        # Do each of the unique checks (unique and unique_together)
        for uclass, unique_check in all_unique_checks:
            seen_data = set()
            for valid_holders in self.valid_holders:
                errors = []
                for name, holder in valid_holders.items():
                    # Get the data for the set of fields that must be unique among the forms in this collection.
                    row_data = [
                        field if field in unique_fields else holder.cleaned_data[field]
                        for field in unique_check
                        if field in holder.cleaned_data
                    ]
                    # Reduce Model instances to their primary key values
                    row_data = tuple(
                        d._get_pk_val() if hasattr(d, '_get_pk_val')
                        # Prevent "unhashable type: list" errors later on.
                        else tuple(d) if isinstance(d, list) else d
                        for d in row_data
                    )
                    if row_data and None not in row_data:
                        # if we've already seen it then we have a uniqueness failure
                        if row_data in seen_data:
                            # poke error messages into the right places and mark the form as invalid
                            errors.append(self.get_unique_error_message(unique_check))
                            holder._errors[NON_FIELD_ERRORS] = errors
                            # Remove the data from the cleaned_data dict since it was invalid.
                            for field in unique_check:
                                if field in holder.cleaned_data:
                                    del holder.cleaned_data[field]
                        # mark the data as seen
                        seen_data.add(row_data)

    def get_unique_error_message(self, unique_check):
        if len(unique_check) == 1:
            return gettext_lazy("Please correct the duplicate data for {0}.").format(*unique_check)
        else:
            fields = get_text_list(unique_check, gettext_lazy("and"))
            return gettext_lazy("Please correct the duplicate data for {0}, which must be unique.").format(fields)

    def validate_siblings_count(self):
        if not self.has_many or self.marked_for_removal:
            return
        num_valid_siblings = reduce(
            operator.add,
            (all(not h.marked_for_removal for h in vh.values()) for vh in self.valid_holders),
            0
        )
        collection_name = self.legend if self.legend else self.__class__.__name__
        if num_valid_siblings < self.min_siblings:
            self._errors.clear()
            msg = gettext_lazy("Not enough entries in “{collection_name}”, please add another.")
            self._errors.append({COLLECTION_ERRORS: [msg.format(collection_name=collection_name)]})
        if self.max_siblings and num_valid_siblings > self.max_siblings:
            self._errors.clear()
            msg = gettext_lazy("Too many entries in “{collection_name}”, please remove one.")
            self._errors.append({COLLECTION_ERRORS: [msg.format(collection_name=collection_name)]})

    def retrieve_instance(self, data):
        """
        Hook to retrieve the main object for a multi object collection.
        """
        return self.instance

    def clean(self):
        return self.cleaned_data

    @property
    def cleaned_data(self):
        """
        Return the cleaned data for this collection and nested forms/collections.
        """
        if not self.is_valid():
            raise AttributeError(f"'{self.__class__}' object has no attribute 'cleaned_data'")
        if self.has_many:
            return [{name: holder.cleaned_data} for valid_holders in self.valid_holders for name, holder in valid_holders.items()]
        else:
            return {name: holder.cleaned_data for name, holder in self.valid_holders.items()}

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

    def model_to_dict(self, instance):
        """
        Create initial data from a starting instance. This instance may be traversed recusively and shall be used to
        fill the initial data for all its sub-collections and forms.
        Forms which do not correspond to the model given by the starting instance, are themselves responsible to
        access the proper referenced models by following the reverse relations through the given foreign keys.
        """
        object_data = {}
        for name, holder in self.declared_holders.items():
            if getattr(holder, 'has_many', False):
                if related_manager := getattr(instance, holder._name, None):
                    try:
                        queryset = related_manager.all()
                    except ValueError:
                        pass
                    else:
                        object_data[name] = holder.models_to_list(queryset)
            else:
                if callable(getattr(holder, 'model_to_dict', None)):
                    object_data[name] = holder.model_to_dict(instance)
                elif isinstance(holder, BaseModelForm):
                    opts = holder._meta
                    object_data[name] = model_to_dict(instance, opts.fields, opts.exclude)
                else:
                    object_data[name] = model_to_dict(instance)
        return object_data

    def models_to_list(self, queryset):
        """
        Create initial data from a queryset. This queryset is traversed recusively and shall be
        used to fill the initial data for this collection and all its sub-collections and forms.

        Forms and Collections which do not correspond to the model given by the starting instance,
        are responsible themselves to override this method in order to access the proper referenced
        models by following the reverse relations through the given foreign keys.
        """
        assert self.has_many, "Method `models_to_list()` can be applied only on a collection with siblings"
        data = [self.model_to_dict(instance) for instance in queryset.all()]
        return data

    def construct_instance(self, instance=None):
        """
        Construct the main instance and all its related objects from the nested dictionary. This
        method may only be called after the current form collection has been validated, usually by
        calling `is_valid`.

        Forms and Collections which do not correspond to the model given by the starting instance,
        are responsible themselves to override this method in order to store the corresponding data
        inside their related models.
        """
        assert self.is_valid(), f"Can not construct instance with invalid collection {self.__class__} object"
        if self.has_many:
            for valid_holders in self.valid_holders:
                # first, handle holders which are forms
                for name, holder in valid_holders.items():
                    if not isinstance(holder, BaseModelForm):
                        continue
                    if holder.marked_for_removal:
                        holder.instance.delete()
                        continue
                    construct_instance(holder, holder.instance)
                    if getattr(self, 'related_field', None):
                        setattr(holder.instance, self.related_field, instance)
                    try:
                        holder.save()
                    except (IntegrityError, ValueError) as error:
                        # some errors are caught only after attempting to save
                        holder._update_errors(error)

                # next, handle holders which are sub-collections
                for name, holder in valid_holders.items():
                    if callable(getattr(holder, 'construct_instance', None)):
                        holder.construct_instance(holder.instance)
        else:
            for name, holder in self.valid_holders.items():
                if callable(getattr(holder, 'construct_instance', None)):
                    holder.construct_instance(instance)
                elif isinstance(holder, BaseModelForm):
                    opts = holder._meta
                    holder.cleaned_data = self.cleaned_data[name]
                    holder.instance = instance
                    construct_instance(holder, instance, opts.fields, opts.exclude)
                    try:
                        holder.save()
                    except IntegrityError as error:
                        holder._update_errors(error)

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
