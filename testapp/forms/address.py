from django.forms import fields, forms


class AddressForm(forms.Form):
    recipient = fields.CharField(
        label="Recipient",
        max_length=100,
    )

    postal_code = fields.CharField(
        label="Postal Code",
        max_length=8,
    )

    city = fields.CharField(
        label="City",
        max_length=50,
    )


