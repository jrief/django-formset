from django.forms import fields, forms

from formset.widgets import DecimalUnitInput


class PriceForm(forms.Form):
    """
    How to use the ``DecimalUnitInput`` widget.
    """
    price = fields.DecimalField(
        label="Price",
        widget=DecimalUnitInput(prefix='€', fixed_decimal_places=True),
        initial=12345.60,
        min_value=-1000,
        decimal_places=2,
        #max_digits=10,
        step_size=10,
    )
