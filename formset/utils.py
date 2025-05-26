import copy
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model, ObjectDoesNotExist, QuerySet
from django.db.models.fields.files import FieldFile, FileField as FileModelField
from django.db.models.utils import AltersData
from django.forms.fields import FileField as FileFormField
from django.forms.forms import BaseForm
from django.forms.models import BaseModelForm, ModelChoiceField, ModelMultipleChoiceField
from django.forms.utils import ErrorDict, ErrorList, RenderableMixin
from django.utils.safestring import mark_safe

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

    def __repr__(self):
        client_messages = getattr(self, 'client_messages', '')
        return f'<{self.__class__.__name__}: {[item for item in self]} {client_messages}>'


def prepare_initial(instance, field_name, field, value):
    """
    Prepare initial data from a serialized representation to be usable for fields requiring an object.
    This function converts entities into a `FieldFile`, `ModelChoiceField`, `ModelMultipleChoiceField` object
    or leaves the value as is.
    """
    if isinstance(field, ModelMultipleChoiceField):
        try:
            Model = apps.get_model(value['model'])
            return Model.objects.filter(
                pk__in=value['p_keys']
            )
        except (KeyError, TypeError):
            return
    elif isinstance(field, ModelChoiceField):
        try:
            Model = apps.get_model(value['model'])
            return Model.objects.get(pk=value['pk'])
        except (KeyError, ObjectDoesNotExist, TypeError):
            pass
    elif isinstance(field, FileFormField):
        return FieldFile(instance, FileModelField(name=field_name), value)
    else:
        return field.to_python(value)


class HolderMixin:
    ignore_marked_for_removal = getattr(settings, 'FORMSET_IGNORE_MARKED_FOR_REMOVAL', False)
    marked_for_removal = False
    partial = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def replicate(self, data=None, initial=None, auto_id=None, prefix=None, instance=None, partial=None, renderer=None,
                  ignore_marked_for_removal=None):

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
        if auto_id:
            replica.auto_id = auto_id
        if prefix:
            replica.prefix = prefix
        if instance:
            replica.instance = instance
        if partial is not None:
            replica.partial = partial
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


class FileFieldMixin:
    """
    Mixin class added by BoundField to fields inheriting from `django.forms.fields.FileField`.
    """

    def _clean_bound_field(self, bf):
        value = bf.initial if self.disabled else bf.data
        instance = AltersData()  # collectionField has no instance, so create a dummy
        if isinstance(value, Path):
            if bf.initial:
                initial = copy.copy(bf.initial)
                initial.name = str(value)
                return initial
            return FieldFile(instance, FileModelField(name=bf.name), str(value))
        elif value is None:
            return FieldFile(instance, FileModelField(name=bf.name), None)
        return self.clean(value, bf.initial)


class RenderableDetachedFieldMixin(RenderableMixin):
    """
    Mixin class to be added to detached fields, if used outside a native Django Form.
    This is required to render a field without converting it to a `BoundField`.
    """

    def get_context(self):
        return {
            'field': self,
        }

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """
        Render the field by rendering the passed widget, adding any HTML
        attributes passed as attrs. If a widget isn't specified, use the
        field's default widget.
        """
        widget = widget or self.widget
        attrs = attrs or {}
        if self.disabled:
            attrs['disabled'] = True
        if '%s' in str(self.auto_id):
            auto_id = self.auto_id % self._name
        elif self.auto_id:
            auto_id = self.auto_id
        else:
            auto_id = ''
        if auto_id:
            attrs['id'] = auto_id
            if self.help_text:
                attrs['aria-describedby'] = f'{auto_id}_help_text'
        attrs['label'] = self._name.replace('_', ' ').title() if self.label is None else self.label
        return widget.render(
            name=self._name,
            value=None,
            attrs=attrs,
            renderer=self.renderer,
        )

    def render(self, template_name=None, context=None, renderer=None):
        """Render this detached field as HTML widget."""
        renderer = renderer or self.renderer
        template_name = template_name or 'formset/default/detached_field.html'
        context = context or self.get_context()
        return mark_safe(renderer.render(template_name, context))

    __str__ = render
    __html__ = render


class CollectionFieldMixin:
    """
    Mixin class to be added to CollectionField if it used as a field holding a FormCollection.
    """
    collection = None
    encoder = DjangoJSONEncoder()

    @classmethod
    def pre_serialize(cls, instance, field_name, value):
        """
        Pre-serialize cleaned data recursively to be usable for a JSONField.
        This function
        - stores all entities of `UploadedFile` to disk and returns their file name.
        - converts all `FieldFile` objects to their file name.
        - converts all `Model` and `QuerySet` objects to a serializable representation.
        """
        if isinstance(value, list):
            return [cls.pre_serialize(instance, field_name, val) for val in value]
        if isinstance(value, dict):
            return {key: cls.pre_serialize(instance, field_name, val) for key, val in value.items()}
        if isinstance(value, UploadedFile):
            file_model_field = FileModelField(name=field_name)
            file_model_field.attname = field_name
            field_file = FieldFile(instance, file_model_field, value.name)
            field_file.save(field_file.name, value, save=False)
            return field_file.name
        if isinstance(value, FieldFile):
            return value.name
        if isinstance(value, Model):
            opts = value._meta
            return {
                'model': '{}.{}'.format(opts.app_label, opts.model_name),
                'pk': value.pk,
            }
        if isinstance(value, QuerySet):
            opts = value.model._meta
            return {
                'model': '{}.{}'.format(opts.app_label, opts.model_name),
                'p_keys': list(
                    value.values_list('pk', flat=True)
                ),
            }
        try:
            return cls.encoder.default(value)
        except TypeError:
            return value

    @classmethod
    def traverse_initial(cls, holder, instance, value):
        if value is None:
            return
        if isinstance(value, list):
            return [cls.traverse_initial(holder, instance, item) for item in value]
        assert isinstance(value, dict), "Value must be a dict or list."
        if isinstance(holder, BaseForm):
            return {
                name: prepare_initial(instance, name, field, value[name])
                for name, field in holder.fields.items() if name in value
            }
        return {
            key: cls.traverse_initial(collection, instance, value[key])
            for key, collection in holder.declared_holders.items() if key in value
        }

    @classmethod
    def _check_collection(cls, holder):
        """
        Run this after instantiation to check if the collection does not contain any ModelForm class.
        """
        if isinstance(holder, BaseForm):
            if isinstance(holder, BaseModelForm):
                raise TypeError(f"In {cls} form must be of type Form not {holder.__class__}.")
        else:
            for collection in holder.declared_holders.values():
                cls._check_collection(collection)
