from django.core.exceptions import ValidationError
from django.forms.fields import JSONField
from django.utils.translation import gettext_lazy as _

from formset.widgets.geomap import GeoMapWidget


class GeoMapField(JSONField):
    default_error_messages = {
        'invalid': _("Enter valid GeoJSON."),
    }
    widget = GeoMapWidget

    def clean(self, value):
        cleaned_data = super().clean(value)
        if cleaned_data.get('type') != 'FeatureCollection':
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        if not isinstance(cleaned_data.get('bbox'), list) or len(cleaned_data['bbox']) != 4:
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        if not isinstance(cleaned_data.get('features'), list):
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        return cleaned_data
