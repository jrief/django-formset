import os
import struct
from base64 import b16encode
from datetime import date
from functools import reduce
from operator import or_

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.core.signing import get_cookie_signer
from django.db.models.query_utils import Q
from django.forms.models import ModelChoiceIterator, ModelChoiceIteratorValue
from django.forms.widgets import DateTimeBaseInput, FileInput, Select, SelectMultiple, TextInput
from django.utils.timezone import datetime, now, utc
from django.utils.translation import gettext_lazy as _


class SimpleModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for obj in queryset:
            yield self.choice(obj)


class GroupedModelChoiceIterator(SimpleModelChoiceIterator):
    group_field_name = None

    def choice(self, obj):
        return (
            ModelChoiceIteratorValue(self.field.prepare_value(obj), obj),
            self.field.label_from_instance(obj),
            getattr(obj, self.group_field_name),
        )


class IncompleteSelectMixin:
    """
    Extra interfaces for widgets not loading the complete set of choices.
    """

    choices = ()
    max_prefetch_choices = 250
    search_lookup = None
    group_field_name = None

    def __init__(self, attrs=None, choices=(), search_lookup=None, group_field_name=None):
        if search_lookup:
            self.search_lookup = search_lookup
        if isinstance(self.search_lookup, str):
            self.search_lookup = [self.search_lookup]
        if group_field_name is not None:
            self.group_field_name = group_field_name
        super().__init__(attrs, choices)

    def search(self, search_term):
        try:
            query = reduce(or_, (Q(**{sl: search_term}) for sl in self.search_lookup))
        except TypeError:
            raise ImproperlyConfigured(f"Invalid attribute 'search_lookup' in {self.__class__}.")
        return self.choices.queryset.filter(query)

    def format_value(self, value):
        if value is None:
            return []
        if not isinstance(value, (tuple, list)):
            value = [value]
        return [str(v) if v is not None else "" for v in value]

    def get_context(self, name, value, attrs):
        if isinstance(self.choices, (ModelChoiceIterator, GroupedModelChoiceIterator)):
            if self.choices.queryset.count() > self.max_prefetch_choices:
                attrs = dict(attrs, incomplete=True)
            if self.group_field_name:
                self.optgroups = self._optgroups_model_choice
                self.choices.queryset = self.choices.queryset.order_by(self.group_field_name)
                self.choices.group_field_name = self.group_field_name
                self.choices.__class__ = GroupedModelChoiceIterator
            else:
                self.optgroups = self._options_model_choice
        else:
            self.optgroups = self._optgroups_static_choice
        context = super().get_context(name, value, attrs)
        return context

    def _optgroups_static_choice(self, name, values, attrs=None):
        optgroups = super().optgroups(name, values, attrs)
        return optgroups

    def _options_model_choice(self, name, values, attrs=None):
        values_list = [str(val) for val in values]
        optgroups, counter = [], 0
        for counter, (val, label) in enumerate(self.choices, counter):
            if counter == self.max_prefetch_choices:
                break
            if not isinstance(val, ModelChoiceIteratorValue):
                continue
            val = str(val)
            if selected := val in values_list:
                values_list.remove(val)
            optgroups.append((None, [{'value': val, 'label': label, 'selected': selected}], counter))
        for counter, val in enumerate(values_list, counter):
            try:
                obj = self.choices.queryset.get(pk=val)
            except ObjectDoesNotExist:
                continue
            label = self.choices.field.label_from_instance(obj)
            optgroups.append((None, [{'value': str(val), 'label': label, 'selected': True}], counter))
        return optgroups

    def _optgroups_model_choice(self, name, values, attrs=None):
        values_list = [str(val) for val in values]
        optgroups, prev_group_name, counter = [], '-', 0
        for counter, (val, label, group_name) in enumerate(self.choices, counter):
            if counter == self.max_prefetch_choices:
                break
            if not isinstance(val, ModelChoiceIteratorValue):
                continue
            val = str(val)
            if selected := val in values_list:
                values_list.remove(val)
            if prev_group_name != group_name:
                prev_group_name = group_name
                subgroup = [{'value': val, 'label': label, 'selected': selected}]
                optgroups.append((group_name, subgroup, counter))
            else:
                subgroup.append({'value': val, 'label': label, 'selected': selected})
        for counter, val in enumerate(values_list, counter):
            try:
                obj = self.choices.queryset.get(pk=val)
            except ObjectDoesNotExist:
                continue
            label = self.choices.field.label_from_instance(obj)
            group_name = getattr(obj, self.group_field_name) if self.group_field_name else None
            optgroup = list(filter(lambda item: item[0] == group_name, optgroups))
            if optgroup:
                optgroup[-1][1].append({'value': str(val), 'label': label, 'selected': True})
            else:
                subgroup = [{'value': str(val), 'label': label, 'selected': True}]
                optgroups.append((group_name, subgroup, counter))
        return optgroups


class Selectize(IncompleteSelectMixin, Select):
    """
    Render widget suitable for TomSelect
    """
    template_name = 'formset/default/widgets/selectize.html'
    placeholder = _("Select")

    def __init__(self, attrs=None, choices=(), search_lookup=None, group_field_name=None, placeholder=None):
        super().__init__(attrs, choices, search_lookup, group_field_name)
        if placeholder is not None:
            self.placeholder = placeholder

    def build_attrs(self, base_attrs, extra_attrs):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if self.is_required:
            attrs['required'] = True  # Selectize overrides the default behaviour
        return attrs

    def _optgroups_static_choice(self, name, values, attrs=None):
        options = [(None, [{'value': '', 'label': self.placeholder}], None)]
        options.extend(super()._optgroups_static_choice(name, values, attrs))
        return options

    def _options_model_choice(self, name, values, attrs=None):
        options = [(None, [{'value': '', 'label': self.placeholder}], None)]
        options.extend(super()._options_model_choice(name, values, attrs))
        return options

    def _optgroups_model_choice(self, name, values, attrs=None):
        optgroups = [(None, [{'value': '', 'label': self.placeholder}], None)]
        optgroups.extend(super()._optgroups_model_choice(name, values, attrs))
        return optgroups


class SelectizeMultiple(Selectize):
    allow_multiple_selected = True
    max_items = 5

    def __init__(self, max_items=None, **kwargs):
        super().__init__(**kwargs)
        if max_items:
            self.max_items = max_items

    def build_attrs(self, base_attrs, extra_attrs):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['max_items'] = self.max_items
        return attrs


class DualSelector(IncompleteSelectMixin, SelectMultiple):
    """
    Render widget suitable for the <select is="django-dual-selector"> widget
    """
    template_name = 'formset/default/widgets/dual_selector.html'


class DualSortableSelector(DualSelector):
    """
    Render widget suitable for the <select is="django-dual-sortable-selector"> widget
    """
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['is_sortable'] = True
        return context


class SlugInput(TextInput):
    def __init__(self, populate_from, attrs=None):
        super().__init__(attrs)
        self.attrs.update({
            'is': 'django-slug',
            'pattern': '^[-a-zA-Z0-9_]+$',
            'populate-from': populate_from,
        })


class UploadedFileInput(FileInput):
    """
    Widget to be used as a replacement for fields of type :class:`django.forms.fields.FileField`
    and :class:`django.forms.fields.ImageField`.
    It converts the submitted POST data to reference the already uploaded file in the directory
    configured for temporary uploads.
    """
    template_name = 'formset/default/widgets/file.html'

    def format_value(self, value):
        return value

    def value_from_datadict(self, data, files, name):
        handle = data.get(name)
        if isinstance(handle, (UploadedFile, bool)):
            return handle
        if hasattr(handle, '__iter__'):
            handle = next(iter(handle), None)
        if isinstance(handle, dict):
            if not handle:
                return False  # marked as deleted
            if 'upload_temp_name' not in handle:
                return
            # file has just been uploaded
            signer = get_cookie_signer(salt='formset')
            upload_temp_name = signer.unsign(handle['upload_temp_name'])
            file = open(default_storage.path(upload_temp_name), 'rb')
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            # create pseudo unique prefix to avoid file name collisions
            epoch = datetime(2022, 1, 1, tzinfo=utc)
            prefix = b16encode(struct.pack('f', (now() - epoch).total_seconds())).decode('utf-8')
            filename = '.'.join((prefix, handle['name']))
            files[name] = UploadedFile(
                file=file, name=filename, size=size, content_type=handle['content_type'],
                content_type_extra=handle['content_type_extra'],
            )
        return files.get(name)


class DateInput(DateTimeBaseInput):
    """
    This is a replacement for Django's date widget ``django.forms.widgets.DateInput`` which renders
    as ``<input type="text" ...>`` . Since we want to use the browsers built-in validation and
    optionally its date-picker, we have to use this alternative implementation.
    """
    template_name = 'django/forms/widgets/date.html'

    def __init__(self, attrs=None):
        default_attrs = {'type': 'date', 'pattern': r'\d{4}-\d{2}-\d{2}'}
        if attrs:
            default_attrs.update(**attrs)
        super().__init__(attrs=default_attrs)

    def format_value(self, value):
        if isinstance(value, date):
            return value.isoformat()
