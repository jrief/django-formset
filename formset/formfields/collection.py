from django.forms.fields import Field

from formset.collection import BaseFormCollection
from formset.utils import CollectionFieldMixin
from formset.widgets import CollectionWidget


class CollectionField(CollectionFieldMixin, Field):
    widget = CollectionWidget

    def __init__(self, collection, label=None, *args, **kwargs):
        if isinstance(collection, type):
            collection = collection()
        if not isinstance(collection, BaseFormCollection):
            raise TypeError("CollectionField requires a FormCollection instance.")
        CollectionFieldMixin._check_collection(collection)
        self.collection = collection
        if label is None:
            # collections do not need a label since each of their fields have their own
            label = ''
        super().__init__(label=label, *args, **kwargs)

    def clean(self, value):
        collection = self.collection.replicate(data=value)
        collection.full_clean()
        return collection.cleaned_data
