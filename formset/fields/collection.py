from django.forms.fields import Field
from formset.widgets import CollectionWidget


class CollectionField(Field):
    collection = None
    widget = CollectionWidget

    def __init__(self, collection, label=None, *args, **kwargs):
        if type(collection.__class__) == type:
            collection = collection()
        self.collection = collection
        if label is None:
            label = ""
        super().__init__(label=label, *args, **kwargs)

    def clean(self, value):
        collection = self.collection.replicate(data=value)
        collection.full_clean()
        return collection.cleaned_data
