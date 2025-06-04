from django.db.models.fields.files import FieldFile, FileField as FileModelField
from django.db.models.utils import AltersData
from django.utils.datastructures import MultiValueDict

from formset.upload import get_file_info


def persit_uploaded_file(richtext_field, field_name, file_upload_widget, content):
    """
    Persists an uploaded file in the directory specified by richtext_field.
    """
    if isinstance(content.get('dataset'), dict) and 'upload_temp_name' in content['dataset']:
        files = MultiValueDict()
        instance = AltersData()  # FileField has no instance, so create a dummy
        file_model_field = FileModelField(
            name=field_name,
            upload_to=richtext_field.upload_to,
            storage=richtext_field.storage
        )
        datadict = {field_name: [content['dataset']]}
        uploaded_file = file_upload_widget.value_from_datadict(datadict, files, field_name)
        field_file = FieldFile(instance, file_model_field, uploaded_file.name)
        file_model_field.attname = field_name
        field_file.save(field_file.name, uploaded_file, save=False)
        file_info = get_file_info(field_file)
        content_type_extra = content['dataset'].get('content_type_extra', {})
        content['dataset'] = dict(file_info, content_type_extra=content_type_extra)
        content['src'] = file_info['download_url']
