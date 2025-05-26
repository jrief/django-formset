from django.forms.fields import Field

from formset.utils import HolderMixin
from formset.widgets import Button


class Activator(HolderMixin, Field):
    default_renderer = None
    widget = Button(action='activate')

    def __init__(self, renderer=None, **kwargs):
        self.renderer = renderer or self.default_renderer
        kwargs.update(
            required=False,
            validators=[],
            label_suffix='',
        )
        super().__init__(**kwargs)
