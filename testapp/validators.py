from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile


def allow_jpeg_only(value):
    if isinstance(value, FieldFile):
        filename = value.name.lower()
        if not (filename.endswith('.jpg') or filename.endswith('.jpeg')):
            raise ValidationError("Only images of type JPEG are allowed.")


def allow_image_only(value):
    if isinstance(value, FieldFile):
        filename = value.name.lower()
        if not (filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png')):
            raise ValidationError("Only images of type JPEG and PNG are allowed.")


def allow_pdf_only(value):
    if isinstance(value, FieldFile):
        filename = value.name.lower()
        if not (filename.endswith('.pdf')):
            raise ValidationError("Only files of type PDF are allowed.")
