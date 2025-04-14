from django.forms.widgets import Widget


class CollectionWidget(Widget):
    """
    Widget to be used by :class:`formset.collection.CollectionField`.
    """
    template_name = 'formset/default/widgets/collection.html'

    def get_context(self, name, value, attrs):
        return {
            'collection': value,
        }
