from django.forms import fields, forms

from formset.formfields.ranges import DualIntegerRangeField


class RangeForm(forms.Form):
    """
    How to use the ``DualNumberRangeInput`` widget.
    """
    range = DualIntegerRangeField(
        label="Range",
    )
