from django.forms import fields, forms

from formset.widgets import SlugInput


class ArticleForm(forms.Form):
    """
    Using a ``SlugField``
    ---------------------

    In Django's Admin, a ``SlugField`` can be configured to be prepopulated using the content of
    another text input field. To emulate a similar behaviour, **django-formset** provides a special
    widget named ``SlugInput``.

    .. code-block:: python

        from django.forms import fields, forms

        class ArticleForm(...):
            ...
            title = fields.CharField(
                label="Title",
                max_length=100,
            )

            slug = fields.SlugField(
                label="Slug",
                widget=SlugInput('title'),
            )
            ...

    This widget takes a single attribute with the name of another field of the same form.
    That field's input value then is used to prepopulate the slug field, where the generated value
    is produced by concatenating the values of the source fields, and then by transforming that
    result into a valid slug (e.g. substituting dashes for spaces, lowercasing letters and rewriting
    unicode characters to ASCII letters).

    Prefilled slug fields aren't modified after a value has been saved as this usually is undesired
    behaviour.
    """

    title = fields.CharField(
        label="Title",
        max_length=100,
    )

    slug = fields.SlugField(
        label="Slug",
        widget=SlugInput('title'),
    )
