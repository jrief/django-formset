.. _slug-input:

================
Slug Input Field
================

This widget is used to create a "slug" using the value of another input field, which typically is a
text field. It usually is used as the browser's counterpart for a Django SlugField_.

The Django Admin provides such client-side functionality, where one can specify that (slug) field to
be prepopulated using the content of another text input field. To emulate a similar behavior,
**django-formset** provides a special widget named ``SlugInput``.

.. _SlugField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#slugfield

.. django-view:: blog_form

    from django.forms import fields, forms
    from formset.widgets import SlugInput

    class BlogForm(forms.Form):
        title = fields.CharField(
            label="Title",
            max_length=100,
        )

        slug = fields.SlugField(
            label="Slug",
            widget=SlugInput('title'),
        )

This widget takes a single attribute with the name of another field of the same form. That field's
input value then is used to prepopulate the slug field, where the generated value is produced by
concatenating the values of the source fields, and then by transforming that result into a valid
slug (e.g. substituting dashes for spaces, lowercasing letters and rewriting unicode characters to
ASCII letters).

Prefilled slug fields aren't modified after a value has been saved as this usually is undesired
behavior.

.. django-view:: blog_view
	:view-function: BlogView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'blog-result'}, form_kwargs={'auto_id': 'bl_id_%s'})
	:hide-code:

	from formset.views import FormView 

	class BlogView(FormView):
	    form_class = BlogForm
	    template_name = "form.html"
	    success_url = "/success"


Implementation
==============

This implementation of the ``SlugInput`` widget is based on the JavaScript library slug_ by Rich
Trott and contributors.

.. _slug: https://www.npmjs.com/package/slug
