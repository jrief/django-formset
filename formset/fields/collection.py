from formset.collection import BaseFormCollection, FormCollectionMeta
from formset.utils import CollectionFieldBase
from formset.widgets import CollectionWidget


class CollectionField(CollectionFieldBase, BaseFormCollection, metaclass=FormCollectionMeta):
    widget = CollectionWidget
