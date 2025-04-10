import copy
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.fields import Field, FileField as FileFormField
from django.forms.forms import Form
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from django.forms.utils import ErrorDict, ErrorList, RenderableMixin
from django.db.models import Model, ObjectDoesNotExist, QuerySet
from django.db.models.fields.files import FieldFile, FileField as FileModelField
from django.db.models.utils import AltersData
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


def post_serialize(instance, field_name, value):
    """
    Post-serialize the POST data recursively to be usable for a JSONField.
    This function
    - stores all entities of `UploadedFile` to disk and returns their file name.
    - converts all `FieldFile` objects to their file name.
    - converts all `ModelChoiceField` and `ModelMultipleChoiceField` objects to a serializable representation.
    """
    if isinstance(value, list):
        return [post_serialize(instance, field_name, val) for val in value]
    if isinstance(value, dict):
        return {key: post_serialize(instance, field_name, val) for key, val in value.items()}
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
        return post_serialize.encoder.default(value)
    except TypeError:
        return value

post_serialize.encoder = DjangoJSONEncoder()


class HolderMixin:
    ignore_marked_for_removal = getattr(settings, 'FORMSET_IGNORE_MARKED_FOR_REMOVAL', False)
    marked_for_removal = False
    partial = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def replicate(self, data=None, initial=None, auto_id=None, prefix=None, instance=None, partial=None, renderer=None,
                  ignore_marked_for_removal=None):
        # print("replicate: ", self.__class__, prefix, initial)
        replica = copy.copy(self)
        if hasattr(self, 'declared_holders'):
            replica.declared_holders = {
                key: holder.replicate(
                    renderer=renderer,
                    ignore_marked_for_removal=ignore_marked_for_removal,
                ) for key, holder in self.declared_holders.items()
            }
            # some initial values must be converted to Python types
            if self.has_many is True and isinstance(initial, list):
                # replica.initial = []
                # for item in initial:
                #     replica.initial.append({})
                #     for key, holder in self.declared_holders.items():
                #         if key not in item:
                #             continue
                #         if isinstance(holder, Form):
                #             replica.initial[-1].update({key: {
                #                 name: prepare_initial(instance, name, field, item[key][name])
                #                 for name, field in holder.fields.items() if name in item[key]
                #             }})
                #         else:
                #             replica.initial[-1].update({key: {
                #                 name: item[key][name]
                #                 for name, field in holder.declared_holders.items() if name in item[key]
                #             }})

                replica.initial = [{
                    key: {
                        name: prepare_initial(instance, name, field, item[key][name])
                        for name, field in holder.fields.items() if name in item[key]
                    } if isinstance(holder, Form) else {
                        name: item[key][name]
                        for name in holder.declared_holders if name in item[key]
                    } for key, holder in self.declared_holders.items() if key in item
                } for item in initial]
            elif self.has_many is False and isinstance(initial, dict):
                replica.initial = {
                    key: {
                        name: prepare_initial(instance, name, field, initial[key][name])
                        for name, field in holder.fields.items() if name in initial[key]
                    } if isinstance(holder, Form) else {
                        name: initial[key][name]
                        for name in holder.declared_holders if name in initial[key]
                    } for key, holder in self.declared_holders.items() if key in initial
                }
        elif initial:
            replica.initial = initial
        replica.data = data
        replica.is_bound = data is not None
        replica._errors = None
        try:
            delattr(replica, 'cleaned_data')
        except AttributeError:
            pass
        if hasattr(replica, 'files'):
            replica.files.clear()
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
        if isinstance(value, Path):
            if bf.initial:
                initial = copy.copy(bf.initial)
                initial.name = str(value)
                return initial
            # CollectionField has no instance, so create a summy
            instance = AltersData()
            return FieldFile(instance, FileModelField(name=bf.name), str(value))
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


class CollectionFieldBase(Field):
    """
    Mixin class to be added to CollectionField if it used as a field holding a FormCollection.
    """
    def _clean_bound_field(self, bf):
        if self.disabled:
            return bf.initial
        collection = self.replicate(data=bf.data)
        collection.full_clean()
        return post_serialize(bf.form.instance, bf.name, collection.cleaned_data)
