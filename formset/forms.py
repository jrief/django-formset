from django.forms.fields import JSONField
from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass
from django.forms.models import ALL_FIELDS, BaseModelForm, ModelFormMetaclass, fields_for_model
from django.utils.functional import cached_property

from formset.fields.shadow import ShadowField
from formset.fieldset import Fieldset
from formset.utils import CollectionFieldBase, FormsetErrorList, HolderMixin, prepare_initial, post_serialize


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
        attrs = dict(attrs_list, declared_fieldsets=declared_fieldsets)
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


class ModelFormMixin(FormMixin):

    def __init__(self, instance=None, *args, **kwargs):
        def initial_value(field_name, field, value):
            if isinstance(field, CollectionFieldBase):
                if not (renderer := getattr(field, 'renderer', field.default_renderer)):
                    renderer = getattr(self, 'renderer', self.default_renderer)
                return field.replicate(instance=instance, initial=value, prefix=field_name, renderer=renderer)
            else:
                return prepare_initial(instance, field_name, field, value)

        if hasattr(self._meta, 'fields_map') and instance is not None:
            initial = kwargs.get('initial', {})
            for field_name, assigned_fields in self._meta.fields_map.items():
                if isinstance(assigned_fields, list):
                    for af in assigned_fields:
                        value = getattr(instance, field_name).get(af)
                        if value is None:
                            continue
                        initial[af] = initial_value(af, self.base_fields[af], value)
                elif isinstance(assigned_fields, str):
                    # direct mapping of a model field to a form field
                    af = assigned_fields
                    initial[af] = initial_value(af, self.base_fields[af], value)
                else:
                    raise TypeError(f"Invalid type for field {field_name}: {type(assigned_fields)}")
            kwargs['initial'] = initial
        super().__init__(instance=instance, *args, **kwargs)

    def _clean_form(self):
        super()._clean_form()
        if hasattr(self._meta, 'fields_map'):
            mapped_fields = []
            for key, value in self._meta.fields_map.items():
                mapped_fields.extend([key, *(value if isinstance(value, list) else [value])])
            cleaned_data = {
                key: value for key, value in self.cleaned_data.items()
                if key not in mapped_fields
            }
            # move values of mapped fields into JSON
            for field_name, assigned_fields in self._meta.fields_map.items():
                if isinstance(assigned_fields, list):
                    if self.instance and hasattr(self.instance, field_name):
                        cleaned_data[field_name] = getattr(self.instance, field_name) or {}
                    else:
                        cleaned_data[field_name] = {}
                    for af in assigned_fields:
                        if af not in self.cleaned_data:
                            continue
                        cleaned_data[field_name][af] = post_serialize(self.instance, af, self.cleaned_data[af])
                elif isinstance(assigned_fields, str):
                    af = assigned_fields
                    cleaned_data[af] = post_serialize(self.instance, af, self.cleaned_data[af])
            self.cleaned_data = cleaned_data
            print('after clean form:', cleaned_data)


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
