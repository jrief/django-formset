from django.forms import fields, forms

from formset.widgets import DecimalUnitInput


class PriceForm(forms.Form):
    """
    How to use the ``DecimalUnitInput`` widget.
    """
    price = fields.DecimalField(
        label="Price",
        widget=DecimalUnitInput(2, prefix='€', attrs={'step': '0.1'}),
    )
