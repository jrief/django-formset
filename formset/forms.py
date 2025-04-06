from pathlib import Path

from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db.models.fields.files import FieldFile, FileField as FileModelField
from django.forms.fields import JSONField, FileField as FileFormField
from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass
from django.forms.models import (
    ALL_FIELDS,
    BaseModelForm,
    ModelFormMetaclass,
    ModelChoiceField,
    ModelMultipleChoiceField,
    fields_for_model,
)
from django.db.models import Model, ObjectDoesNotExist, QuerySet
from django.utils.functional import cached_property

from formset.fields import ShadowField
from formset.fieldset import Fieldset
from formset.utils import FormsetErrorList, HolderMixin


class FormDecoratorMixin:
    def __init__(self, error_class=FormsetErrorList, **kwargs):
        kwargs['error_class'] = error_class
        super().__init__(**kwargs)

    def __getitem__(self, name):
        "Returns a modified BoundField for the given field."
        from formset.boundfield import BoundField

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
    Mixin class to be added to a form inheriting from a native Django Form.
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


class FormsetMetaclassMixin(type):
    def __new__(mcs, name, bases, attrs):
        attrs_list, declared_fieldsets = [], {}
        for key, value in list(attrs.items()):
            if isinstance(value, Fieldset):
                declared_fieldsets[key] = value
                for field_name, field in value.declared_fields.items():
                    attrs_list.append((f'{key}.{field_name}', field))
            else:
                attrs_list.append((key, value))
        return super().__new__(mcs, name, bases, dict(attrs_list, declared_fieldsets=declared_fieldsets))


class DeclarativeFieldsetMetaclass(FormsetMetaclassMixin, DeclarativeFieldsMetaclass):
    """
    Modified metaclass to collect Fields and Fieldsets from the Form class definition.
    """


class Form(FormMixin, BaseForm, metaclass=DeclarativeFieldsetMetaclass):
    """
    Base class for all Django Form classes.
    """


class ModelFormMixin(FormMixin):
    def __init__(self, instance=None, *args, **kwargs):
        if hasattr(self._meta, 'fields_map') and instance is not None:
            initial = kwargs.get('initial', {})
            for field_name, assigned_fields in self._meta.fields_map.items():
                if isinstance(assigned_fields, list):
                    for af in assigned_fields:
                        reference = getattr(instance, field_name).get(af)
                        field_obj = self.base_fields[af]
                        if isinstance(field_obj, ModelMultipleChoiceField):
                            try:
                                Model = apps.get_model(reference['model'])
                                initial[af] = Model.objects.filter(
                                    pk__in=reference['p_keys']
                                )
                            except (KeyError, TypeError):
                                pass
                        elif isinstance(field_obj, ModelChoiceField):
                            try:
                                Model = apps.get_model(reference['model'])
                                initial[af] = Model.objects.get(pk=reference['pk'])
                            except (KeyError, ObjectDoesNotExist, TypeError):
                                pass
                        elif isinstance(field_obj, FileFormField):
                            initial[af] = FieldFile(instance, FileModelField(name=af), reference)
                        else:
                            initial.setdefault(af, field_obj.to_python(reference))
                elif isinstance(assigned_fields, str):
                    # direct mapping of a model field to a form field
                    field_obj = self.base_fields[assigned_fields]
                    assert not isinstance(field_obj, (ModelChoiceField, ModelMultipleChoiceField))
                    reference = getattr(instance, field_name)
                    if isinstance(field_obj, FileFormField):
                        initial[assigned_fields] = FieldFile(instance, FileModelField(name=assigned_fields), reference)
                    else:
                        initial.setdefault(assigned_fields, field_obj.to_python(reference))
                else:
                    raise TypeError(f"Invalid type for field {field_name}: {type(assigned_fields)}")
            kwargs['initial'] = initial
        super().__init__(instance=instance, *args, **kwargs)

    def _clean_form(self):
        super()._clean_form()
        if hasattr(self._meta, 'fields_map'):
            encoder = DjangoJSONEncoder()
            cleaned_data = {
                key: value for key, value in self.cleaned_data.items()
                if key not in self._meta.fields_map
            }
            for field_name, assigned_fields in self._meta.fields_map.items():
                if isinstance(assigned_fields, list):
                    # Keep other fields in JSON
                    if self.instance and hasattr(self.instance, field_name):
                        cleaned_data[field_name] = getattr(self.instance, field_name) or {}
                    else:
                        cleaned_data[field_name] = {}
                    for af in assigned_fields:
                        if af not in self.cleaned_data:
                            continue
                        if isinstance(self.base_fields[af], ModelMultipleChoiceField) and isinstance(
                            self.cleaned_data[af], QuerySet
                        ):
                            opts = self.cleaned_data[af].model._meta
                            cleaned_data[field_name][af] = {
                                'model': '{}.{}'.format(opts.app_label, opts.model_name),
                                'p_keys': list(
                                    self.cleaned_data[af].values_list('pk', flat=True)
                                ),
                            }
                        elif isinstance(self.base_fields[af], ModelChoiceField) and isinstance(
                            self.cleaned_data[af], Model
                        ):
                            opts = self.cleaned_data[af]._meta
                            cleaned_data[field_name][af] = {
                                'model': '{}.{}'.format(opts.app_label, opts.model_name),
                                'pk': self.cleaned_data[af].pk,
                            }
                        elif isinstance(self.base_fields[af], FileFormField):
                            uploaded_file = self.cleaned_data[af]
                            if isinstance(uploaded_file, UploadedFile):
                                # A file has been uploaded using the FileField mapped onto a JSONField, hence we
                                # must serialize the `UploadedFile` object, otherwise the JSON validator complains.
                                # In method `save()` this serialized description is then converted back to an
                                # `UploadedFile` object.
                                cleaned_data[field_name][af] = {
                                    'uploaded_file_path': uploaded_file.file.name,
                                    'name': uploaded_file.name,
                                    'content_type': uploaded_file.content_type,
                                    'content_type_extra': uploaded_file.content_type_extra,
                                    'size': uploaded_file.size,
                                    'charset': uploaded_file.charset,
                                }
                        else:
                            value = self.base_fields[af].prepare_value(self.cleaned_data[af])
                            try:
                                cleaned_data[field_name][af] = encoder.default(value)
                            except TypeError:
                                cleaned_data[field_name][af] = value
                elif isinstance(assigned_fields, str):
                    value = self.base_fields[assigned_fields].prepare_value(self.cleaned_data[assigned_fields])
                    try:
                        cleaned_data[field_name] = encoder.default(value)
                    except TypeError:
                        cleaned_data[field_name] = value

            self.cleaned_data = cleaned_data

    def save(self, commit=True):
        if hasattr(self._meta, 'fields_map'):
            for field_name, assigned_fields in self._meta.fields_map.items():
                if isinstance(assigned_fields, list):
                    for af in assigned_fields:
                        if isinstance(self.base_fields[af], FileFormField):
                            file_info = self.cleaned_data[field_name][af]
                            if isinstance(file_info, dict) and 'uploaded_file_path' in file_info:
                                # Deserialize the cleaned data back to an `UploadedFile` object so that it can
                                # be stored as a file and used as a `FieldFile` object.
                                file_path = Path(file_info.pop('uploaded_file_path'))
                                file_model_field = FileModelField(name=af)
                                file_model_field.attname = af
                                with file_path.open(mode='rb') as fh:
                                    uploaded_file = UploadedFile(File(fh, name=file_path.name), **file_info)
                                    field_file = FieldFile(self.instance, file_model_field, uploaded_file.name)
                                    field_file.save(field_file.name, uploaded_file, save=False)
                                self.cleaned_data[field_name][af] = field_file.name
        return super().save(commit)


class FormsetModelFormMetaclass(FormsetMetaclassMixin, ModelFormMetaclass):
    """
    Modified metaclass to
    * collect Fields and Fieldsets from the ModelForm class definition.
    * map form fields to a JSONField in the model.
    """
    def __new__(mcs, name, bases, attrs):
        Meta = mcs._find_meta(bases, attrs)

        # Modify fields_map to respect Meta.fields and Meta.exclude
        fields = getattr(Meta, 'fields', None)
        if fields_map := getattr(Meta, 'fields_map', None):
            assert isinstance(fields_map, dict), (
                "fields_map must be a dict of model field names mapped to "
                "a list of form field names or a single form field name."
            )
            fields_map = dict(fields_map)  # copy for modification
            exclude = getattr(Meta, 'exclude', None)
            form_fields = fields_for_model(
                Meta.model,
                fields=None if fields == ALL_FIELDS else fields,
                exclude=exclude,
            )
            Meta.fields = mcs._create_fields_option(form_fields, fields_map)
            for key, value in fields_map.items():
                if isinstance(value, (list, tuple)):
                    fields_map[key] = list(value)
                elif isinstance(value, str):
                    fields_map[key] = value
                else:
                    raise TypeError(f"Invalid type for field {key}: Must be str or list, not {type(value)}")
                attrs[key] = ShadowField()
        disabled_fields = list(getattr(Meta, 'disabled_fields', []))

        if not any(issubclass(base, ModelFormMixin) for base in bases):
            bases = (ModelFormMixin,) + bases
        new_class = super().__new__(mcs, name, bases, dict(attrs, Meta=Meta))

        # disable fields marked as readonly
        for field_name in disabled_fields:
            new_class.base_fields[field_name].disabled = True

        # perform some model checks
        if fields_map:
            for shadowfield_name in fields_map.keys():
                assert isinstance(new_class.base_fields[shadowfield_name], ShadowField)
                if isinstance(fields_map[shadowfield_name], list):
                    for field_name in fields_map[shadowfield_name]:
                        assert (
                            field_name in new_class.base_fields
                        ), "Field {} listed in `{}.Meta.fields_map['{}']` is missing in Form declaration".format(
                            field_name, name, shadowfield_name
                        )
                else:
                    assert isinstance(
                        new_class.base_fields[fields_map[shadowfield_name]],
                        form_fields[shadowfield_name].__class__
                    ), (
                        "Field {} listed in `{}.Meta.fields_map['{}']` is not of the same type as the model field".format(
                        fields_map[shadowfield_name], name, shadowfield_name
                    ))

            new_class._meta.fields_map = fields_map
        return new_class

    @classmethod
    def _find_meta(mcs, bases, attrs):
        """
        Find Meta class in the inheritance chain.
        """
        if Meta := attrs.pop('Meta', None):
            return Meta
        for base in bases:
            for b in base.__mro__:
                if Meta := getattr(b, 'Meta', None):
                    return Meta
        return type('Meta', (), {})

    @classmethod
    def _create_fields_option(mcs, form_fields, fields_map):
        fields = []
        for field_name, form_field in form_fields.items():
            fields.append(field_name)
            if field_name in fields_map:
                if isinstance(form_field, JSONField):
                    assert isinstance(fields_map[field_name], list)
                    fields.extend(fields_map[field_name])
                else:
                    assert isinstance(fields_map[field_name], str)
                    fields.append(fields_map[field_name])
        return fields


class ModelForm(ModelFormMixin, BaseModelForm, metaclass=FormsetModelFormMetaclass):
    """
    Base class for all Django ModelForm classes.
    """
