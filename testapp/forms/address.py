from django.forms import fields, forms

from formset.renderers.bootstrap import FormRenderer as BootstrapFormRenderer


class AddressForm(forms.Form):
    default_renderer = BootstrapFormRenderer(
        form_css_classes='row',
        field_css_classes={'*': 'mb-2 col-12', 'postal_code': 'mb-2 col-4', 'city': 'mb-2 col-8'},
    )

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


