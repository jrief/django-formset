from formset.collection import BaseFormCollection, FormCollectionMeta
from formset.utils import CollectionFieldBase
from formset.widgets import CollectionWidget


class CollectionField(CollectionFieldBase, BaseFormCollection, metaclass=FormCollectionMeta):
    widget = CollectionWidget

    def __init__(self, label=None, *args, **kwargs):
        CollectionFieldBase._check_collection(self)
        if label is None:
            # collections usually do not need a label, since each of their fields have their own
            label = ''
        super().__init__(label=label, *args, **kwargs)
