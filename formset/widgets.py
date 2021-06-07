import os

from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import default_storage
from django.core.signing import get_cookie_signer
from django.forms.widgets import FileInput, Select


class Selectize(Select):
    """
    Render widget suitable
    """
    template_name = 'formset/default/widgets/selectize.html'
    max_prefetch_choices = 50  # TODO: increase

    def get_context(self, name, value, attrs):
        use_endpoint = self.choices.queryset.count() > self.max_prefetch_choices
        context = super().get_context(name, value, attrs)
        options = context['widget'].pop('optgroups')
        context['widget'].update(
            useendpoint=use_endpoint,
            options=options,
        )
        return context

    def optgroups(self, name, value, attrs=None):
        choices = zip(self.choices, range(self.max_prefetch_choices))
        options = [{'value': str(value), 'label': label} for value, label in self.choices]
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
