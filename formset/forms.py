from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
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

from formset.fields.shadow import ShadowField
from formset.fieldset import Fieldset
from formset.utils import CollectionFieldBase, FormsetErrorList, HolderMixin


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
        attrs_list, declared_collections, declared_fieldsets = [], {}, {}
        # prefix = attrs.pop('prefix', None)
        for key, value in list(attrs.items()):
            if isinstance(value, CollectionFieldBase):
                declared_collections[key] = value  # TODO: declared_collections actually is never used
                # attrs_list.append((key, value))
                # if prefix is None:
                #     # if we add a CollectionField, the current form must set a prefix
                #     attrs_list.append(('prefix',name.lower()))
                attrs_list.append((key, value))
            elif isinstance(value, Fieldset):
                declared_fieldsets[key] = value
                for field_name, field in value.declared_fields.items():
                    attrs_list.append((f'{key}.{field_name}', field))
            else:
                attrs_list.append((key, value))
        attrs = dict(attrs_list, declared_fieldsets=declared_fieldsets, declared_collections=declared_collections)
        new_class = super().__new__(mcs, name, bases, attrs)
        return new_class


class DeclarativeFieldsetMetaclass(FormsetMetaclassMixin, DeclarativeFieldsMetaclass):
    """
    Modified metaclass to collect Fields and Fieldsets from the Form class definition.
    """


class Form(FormMixin, BaseForm, metaclass=DeclarativeFieldsetMetaclass):
    """
    Base class for all Django Form classes.
    """

def pre_serialize(instance, field_name, value):
    """
    Pre-serialize the cleaned data recursively to be usable for a JSONField.
    This function
    - stores all entities of `UploadedFile` to disk and returns their file name.
    - converts all `FieldFile` objects to their file name.
    - converts all `ModelChoiceField` and `ModelMultipleChoiceField` objects to a serializable representation.
    """
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [pre_serialize(instance, field_name, val) for val in value]
    if isinstance(value, dict):
        return {key: pre_serialize(instance, field_name, val) for key, val in value.items()}
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


class ModelFormMixin(FormMixin):
    def _prepare_initial(self, instance, field_name, field, value):
        """
        Prepare initial data from a serialized representation to be usable for a CollectionField.
        This function converts entities into a `FieldFile`, `ModelChoiceField` or `ModelMultipleChoiceField` object.
        """
        # if isinstance(value, list):
        #     return [self._prepare_initial(instance, field_name, field, val) for val in value]
        # if isinstance(value, dict):
        #     return {key: self._prepare_initial(instance, key, field, val) for key, val in value.items()}
        if isinstance(field, ModelMultipleChoiceField):
            try:
                Model = apps.get_model(value['model'])
                return Model.objects.filter(
                    pk__in=value['p_keys']
                )
            except (KeyError, TypeError):
                return
        if isinstance(field, ModelChoiceField):
            try:
                Model = apps.get_model(value['model'])
                return Model.objects.get(pk=value['pk'])
            except (KeyError, ObjectDoesNotExist, TypeError):
                pass
        if isinstance(field, FileFormField):
            return FieldFile(instance, FileModelField(name=field_name), value)
        if isinstance(field, CollectionFieldBase):
            if field.has_many and not isinstance(value, list):
                return
            if not field.has_many and not isinstance(value, dict):
                return
            if not (renderer := getattr(field, 'renderer', field.default_renderer)):
                renderer = getattr(self, 'renderer', self.default_renderer)
            # TODO: start recursion
            return field.replicate(
                initial=value,
                prefix=field_name,
                renderer=renderer,
            )

        return field.to_python(value)

    def __init__(self, instance=None, *args, **kwargs):
        if hasattr(self._meta, 'fields_map') and instance is not None:
            initial = kwargs.get('initial', {})
            for field_name, assigned_fields in self._meta.fields_map.items():
                if isinstance(assigned_fields, list):
                    for af in assigned_fields:
                        value = getattr(instance, field_name).get(af)
                        value = self._prepare_initial(instance, af, self.base_fields[af], value)
                        initial.setdefault(af, value)
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
            mapped_fields = []
            for key, value in self._meta.fields_map.items():
                mapped_fields.extend([key, *(value if isinstance(value, list) else [value])])
            cleaned_data = {
                key: value for key, value in self.cleaned_data.items()
                if key not in mapped_fields
            }
            print('before:', cleaned_data)
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

    def _post_clean(self):
        print('post_clean: ', self.cleaned_data)
        for field_name in self._meta.fields_map.keys():
            self.cleaned_data[field_name] = pre_serialize(self.instance, field_name, self.cleaned_data[field_name])
        super()._post_clean()


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
