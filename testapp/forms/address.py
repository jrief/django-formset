from django.forms import fields, forms


class AddressForm(forms.Form):
    """
    Grouping fields using CSS
    -------------------------

    Sometimes it is desirable to align certain input fields in the same row. To achieve this, the Bootstrap
    framework offers special CSS classes, in order to style the input groups into columns of different size.

    We can use this feature, by adding a dictionary to our Form class:

    .. code-block:: python

        from formset.renderers.bootstrap import FormRenderer

        class AddressForm(...):
            ...
            default_renderer = FormRenderer(
                form_css_classes='row',
                field_css_classes={
                    'postal_code': 'mb-2 col-4',
                    'city': 'mb-2 col-8',
                    '*': 'mb-2 col-12',
                },
            })
            ...

    This overwrites the renderer for this Form class. Here the CSS classes for the named fields ``postal_code`` and
    ``city`` replace the given defaults in the HTML element wrapping the input field(s),
    ie. ``<django-field-group class="...">``. The key value ``'*'`` is used as a wildcard matching all other field
    names.
    """

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
