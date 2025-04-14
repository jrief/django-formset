from django.forms.fields import Field

from formset.widgets.models import EmptyWidget


class ShadowField(Field):
    """
    A pseudo field to be used for mimicking a field value, which actually is not rendered inside the form.
    This is required for forms using the `fields_map` option to map a model field to a placeholder.
    """
    widget = EmptyWidget

    def __init__(self, required=False, *args, **kwargs):
        # a ShadowField can not be required
        super().__init__(required=required, *args, **kwargs)
