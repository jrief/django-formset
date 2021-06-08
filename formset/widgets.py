from functools import reduce
from operator import or_
import os

from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from django.core.signing import get_cookie_signer
from django.db.models.query_utils import Q
from django.forms.models import ModelChoiceIterator
from django.forms.widgets import FileInput, Select


class Selectize(Select):
    """
    Render widget suitable
    """
    template_name = 'formset/default/widgets/selectize.html'
    max_prefetch_choices = 50  # TODO: increase
    search_lookup = None

    def __init__(self, attrs=None, choices=(), search_lookup=None):
        if search_lookup:
            self.search_lookup = search_lookup
        if isinstance(self.search_lookup, str):
            self.search_lookup = [self.search_lookup]
        super().__init__(attrs, choices)

    def build_attrs(self, base_attrs, extra_attrs):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        return attrs

    def search(self, search_term):
        try:
            query = reduce(or_, (Q(**{sl: search_term}) for sl in self.search_lookup))
        except TypeError:
            raise ImproperlyConfigured(f"Invalid attribute 'search_lookup' in {self.__class__}.")
        return self.choices.queryset.filter(query)

    def get_context(self, name, value, attrs):
        if isinstance(self.choices, ModelChoiceIterator) and self.choices.queryset.count() > self.max_prefetch_choices:
            attrs = dict(attrs, uncomplete=True)
        context = super().get_context(name, value, attrs)
        options = context['widget'].pop('optgroups')
        context['widget']['options'] = options
        return context

    def optgroups(self, name, value, attrs=None):
        choices = zip(self.choices, range(self.max_prefetch_choices))
        options = [{'value': str(v), 'label': l, 'selected': str(v) in value} for (v, l), _ in choices]
        return options


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
        signer = get_cookie_signer(salt='formset')
        if handle := next(iter(data.get(name, ())), None):
            upload_temp_name = signer.unsign(handle['upload_temp_name'])
            file = open(default_storage.path(upload_temp_name))
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            files[name] = UploadedFile(
                file=file, name=handle['name'], size=size, content_type=handle['content_type'],
                content_type_extra=handle['content_type_extra'],
            )
        return files.get(name)
