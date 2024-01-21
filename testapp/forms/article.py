from django.forms import fields, forms

from formset.widgets import SlugInput


class ArticleForm(forms.Form):
    """
    In Django, a ``SlugField`` can be configured to be prepopulated using the content of another text input
    field. To emulate a similar behaviour, **django-formset** provides a special widget named ``SlugInput``.
    """

    title = fields.CharField(
        label="Title",
        max_length=100,
    )

    slug = fields.SlugField(
        label="Slug",
        widget=SlugInput('title'),
        help_text="The slug will be automatically generated from the title",
    )
