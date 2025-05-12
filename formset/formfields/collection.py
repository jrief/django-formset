from django.core.exceptions import ValidationError
from django.forms.fields import Field

from formset.collection import BaseFormCollection
from formset.utils import CollectionFieldMixin
from formset.widgets import CollectionWidget


class CollectionField(CollectionFieldMixin, Field):
    widget = CollectionWidget

    def __init__(self, collection, label=None, required=None, *args, **kwargs):
        if isinstance(collection, type):
            collection = collection()
        if not isinstance(collection, BaseFormCollection):
            raise TypeError("CollectionField requires a FormCollection instance.")
        CollectionFieldMixin._check_collection(collection)
        self.collection = collection
        if label is None:
            # collections do not need a label since each of their fields have their own
            label = ''
        # CollectionField is never required because their own fields perform the validation
        super().__init__(label=label, required=False, *args, **kwargs)

    def clean(self, value):
        collection = self.collection.replicate(data=value)
        if not collection.is_valid():
            # Django's `ValidationError()` constructor does not support nested fields
            if isinstance(collection._errors, dict):
                validation_error = ValidationError({})
                validation_error.error_dict.update(collection._errors)
            elif isinstance(collection._errors, (dict, list)):
                validation_error = ValidationError([])
                validation_error.error_list.extend(collection._errors)
            else:
                validation_error = ValidationError(collection._errors)
            raise validation_error
        return collection.cleaned_data
