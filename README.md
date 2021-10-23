# django-formset – Better UX for Django Forms 

`<django-formset>` is a [Webcomponent](https://developer.mozilla.org/en-US/docs/Web/Web_Components)
used to wrap one or more Django Forms and/or ModelForms.

## Example

Say, we have a standard Django Form:

```python
from django.forms import forms, fields

class SubscribeForm(forms.Form):
    last_name = fields.CharField(
        label="Last name",
        min_length=2,
        max_length=50,
    )

    # ... more fields
```

then when rendering to HTML, we can wrap that Form into our special Webcomponent:

```html
{% load render_form from formsetify %}

<django-formset endpoint="{{ request.path }}">
  {% render_form form "bootstrap" field_classes="mb-2" %}
  <button type="button" click="disable -> submit -> proceed !~ scrollToError" class="btn">Submit</button>
</django-formset>
```

Instead of using a `<form>`-tag and include all its fields, here we wrap the complete form
inside the special Webcomponent `<django-formset>`. This allows us to communicate via Ajax with
our Django view, using the named endpoint. This means, that we can wrap multiple `<form>`-elements
into our Formset. It also means, that we now can place the Submit `<button>`-element outside of the
`<form>`-element. By doing so, we can decouple the Form's business-logic from its technical
constraint, of transferring a group of fields from and to the server. 

When designing this library, the main goal was to keep the programming interface a near as possible
to the way Django handles Forms, Models and Views.


## Some Highlights

* Before submitting, our Form is prevalidated by the browser, using the constraints we defined for
  each Django Field.
* The Form's data is send by an Ajax request, preventing a full page reload. This gives a much
  better user experience.
* Server side validation errors are sent back to the browser, and rendered near the offending
  Form Field.
* Non-field validation errors are renderer together with the form.
* CSRF-tokens are handlet trough a Cookie, hence there is no need to add that token to each form.
* Forms can be rendered for different CSS frameworks using their specific styleguides for arranging
  HTML. Currently **django-formset** includes renderers for
  [Bootstrap](https://getbootstrap.com/docs/5.0/forms/overview/),
  [Bulma](https://bulma.io/documentation/form/general/),
  [Foundation](https://get.foundation/sites/docs/forms.html),
  [Tailwind](https://tailwindcss.com/) [^1] and [UIKit](https://getuikit.com/docs/form).
* Support for all widgets Django offers, this also includes Radios and multiple checkboxes with
  options.
* File uploads are handled asynchrounosly. This means that the user drags a file to the form, which
  is uploaded immediatly to a temporary folder, returning a unique handle together with a thumbnail
  of the uploaded file. This handle then is used to access that file and proceed as usual.
* Select boxes with too many entries, can be filtered by the server using a search query. No extra
  endpoint is required for this feature.
* Radios and Multiple Checkboxes with only a few fields can be rendered inlined rather than beneath
  each other.
* The Submit buttons can be configured as a chain of actions. It for instance is possible to change
  the CSS depending on success or failure, add delays and specify the further proceeding, for
  instance the success page.
* A Formset can group multiple Forms into a Form-Collection. On submission, this collection then is
  sent to the server as a group a separate entities. After all Forms have been validated, the
  submitted data is provided as a nested Python dictionary.
* Such a Form-Collection can be declared to have many entities. This allows to create siblings of
  Forms, similar the Django's Admin Inline Forms. However, each of these siblings can contain other
  Form-Collections, which themselves can also be declared as siblings. It is possible to change the
  number of siblings using one "Add" and multiple "Remove" buttons.
* The client part, has no dependencies to any JavaScript-framework. It is written completely in
  pure TypeScript and cleanely compiles to a single, portable JS-file.

[^1]: Tailwind is special here, it doesn't include purpose-built form control classes out of the
      box. Instead **django-formset** adds an opinionated set of CSS classes suitable for Tailwind.


## Documentation

Not deployed on RTD, but some documentation can be found in the `docs` folder.


## Motivation

This library shall replace the Form-validation framework in django-angular.


[![Build Status](https://github.com/jrief/django-formset/actions/workflows/pythonpackage.yml/badge.svg)]()
[![PyPI](https://img.shields.io/pypi/pyversions/django-entangled.svg)]()
[![PyPI version](https://img.shields.io/pypi/v/django-entangled.svg)](https://https://pypi.python.org/pypi/django-entangled)
[![PyPI](https://img.shields.io/pypi/l/django-entangled.svg)]()
