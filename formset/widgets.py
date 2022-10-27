import os
import struct
from base64 import b16encode
from functools import reduce
from operator import or_

from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.core.signing import get_cookie_signer
from django.db.models.query_utils import Q
from django.forms.models import ModelChoiceIterator, ModelChoiceIteratorValue
from django.forms.widgets import FileInput, Select, SelectMultiple, TextInput
from django.utils.timezone import datetime, now, utc
from django.utils.translation import gettext_lazy as _


class IncompleteSelectMixin:
    """
    Extra interfaces for widgets not loading the complete set of choices.
    """

    choices = ()
    max_prefetch_choices = 250
    search_lookup = None

    def __init__(self, attrs=None, choices=(), search_lookup=None):
        if search_lookup:
            self.search_lookup = search_lookup
        if isinstance(self.search_lookup, str):
            self.search_lookup = [self.search_lookup]
        super().__init__(attrs, choices)

    def search(self, search_term):
        try:
            query = reduce(or_, (Q(**{sl: search_term}) for sl in self.search_lookup))
        except TypeError:
            raise ImproperlyConfigured(f"Invalid attribute 'search_lookup' in {self.__class__}.")
        return self.choices.queryset.filter(query)

    def get_context(self, name, value, attrs):
        if isinstance(self.choices, ModelChoiceIterator):
            self.optgroups = self._optgroups_model_choice
            if self.choices.queryset.count() > self.max_prefetch_choices:
                attrs = dict(attrs, incomplete=True)
        else:
            self.optgroups = self._optgroups_static_choice
        context = super().get_context(name, value, attrs)
        options = context['widget'].pop('optgroups')
        context['widget']['options'] = options
        return context

    def _optgroups_static_choice(self, name, values, attrs=None):
        options = []
        for val, label in self.choices:
            val = str(val)
            if val in values:
                options.append({'value': val, 'label': label, 'selected': True})
            else:
                options.append({'value': val, 'label': label})
        return options

    def _optgroups_model_choice(self, name, values, attrs=None):
        values_set = set(values)
        options = [{}] * len(values_set)
        counter = 0
        for val, label in self.choices:
            if not isinstance(val, ModelChoiceIteratorValue):
                continue
            val = str(val)
            if val in values_set:
                index = values.index(val)
                if index < len(options):
                    options[index] = {'value': val, 'label': label, 'selected': True}
                values_set.remove(val)
            elif counter < self.max_prefetch_choices:
                options.append({'value': val, 'label': label})
            elif not values_set:
                break
            counter += 1
        return options


class Selectize(IncompleteSelectMixin, Select):
    """
    Render widget suitable for TomSelect
    """
    template_name = 'formset/default/widgets/selectize.html'
    placeholder = _("Select")

    def __init__(self, attrs=None, choices=(), search_lookup=None, placeholder=None):
        super().__init__(attrs, choices, search_lookup)
        if placeholder is not None:
            self.placeholder = placeholder

    def build_attrs(self, base_attrs, extra_attrs):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        if self.is_required:
            attrs['required'] = True  # Selectize overrides the default behaviour
        return attrs

    def _optgroups_static_choice(self, name, values, attrs=None):
        options = [{'value': '', 'label': self.placeholder}]
        options.extend(super()._optgroups_static_choice(name, values, attrs))
        return options

    def _optgroups_model_choice(self, name, values, attrs=None):
        options = [{'value': '', 'label': self.placeholder}]
        options.extend(super()._optgroups_model_choice(name, values, attrs))
        return options


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
