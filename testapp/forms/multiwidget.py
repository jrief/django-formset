from django import forms

from formset.forms import Form


class PhoneWidget(forms.MultiWidget):

    def __init__(self, attrs=None):
        super().__init__(
            widgets=[forms.TextInput, forms.TextInput, forms.TextInput],
            attrs=attrs,
        )

    def decompress(self, value):
        if value is None:
            return ['', '', '']
        return value.split('-')


class PhoneField(forms.MultiValueField):

    widget = PhoneWidget()

    def __init__(self, **kwargs):
        super().__init__(fields=(forms.CharField(), forms.CharField(), forms.CharField()), **kwargs)

    def compress(self, data_list):
        return '-'.join(data_list)


CURRENCY_CHOICES = [('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP')]


class PriceWidget(forms.MultiWidget):
    """
    Simulates a mixed MultiWidget with a TextInput (amount) and a Select
    (currency). Before the fix, the Select element overwrote the TextInput in
    fieldElements, making the amount value unrecoverable.
    """

    def __init__(self, attrs=None):
        super().__init__(
            widgets=[
                forms.TextInput(attrs={'placeholder': 'Amount'}),
                forms.Select(choices=CURRENCY_CHOICES),
            ],
            attrs=attrs,
        )

    def decompress(self, value):
        if value is None:
            return ['', 'USD']
        parts = str(value).split(' ', 1)
        return parts if len(parts) == 2 else [value, 'USD']


class PriceField(forms.MultiValueField):

    widget = PriceWidget()

    def __init__(self, **kwargs):
        super().__init__(
            fields=(
                forms.DecimalField(min_value=0),
                forms.ChoiceField(choices=CURRENCY_CHOICES),
            ),
            **kwargs,
        )

    def compress(self, data_list):
        if data_list and len(data_list) == 2:
            return f"{data_list[0]} {data_list[1]}"
        return ''


class MultiWidgetForm(Form):
    name = forms.CharField()
    phone_numbers = PhoneField(label="Phone Numbers")
    price = PriceField(label="Price")
