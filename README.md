# django-formset – Better UX for Django Forms 

This library handles single forms and sets of forms in an alternative way as Django does it
providing [formsets](https://docs.djangoproject.com/en/stable/topics/forms/formsets/). It however
implements them with a way better user experience using modern form functionality as provided with
HTML5.

[![Build Status](https://github.com/jrief/django-formset/actions/workflows/tests.yml/badge.svg)](https://github.com/jrief/django-formset/actions)
[![PyPI version](https://img.shields.io/pypi/v/django-formset.svg)](https://pypi.python.org/pypi/django-formset)
[![Django versions](https://img.shields.io/pypi/djversions/django-formset)](https://pypi.python.org/pypi/django-formset)
[![Python versions](https://img.shields.io/pypi/pyversions/django-formset.svg)](https://pypi.python.org/pypi/django-formset)
[![Software license](https://img.shields.io/pypi/l/django-formset.svg)](https://github.com/jrief/django-formset/blob/master/LICENSE)

Let's explain it using a short example. Say, we have a Django form with three fields:

```python
from django.forms import fields, forms

class AddressForm(forms.Form):
    recipient = fields.CharField(label="Recipient")
    postal_code = fields.CharField("Postal Code")
    city = fields.CharField(label="City")
```

After creating a
[Django FormView](https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#django.views.generic.edit.FormView)
we can render the above form using a slightly modified template:

```html
{% load formsetify %}
{% render_form form "bootstrap" %}
```

This will render our form using the layout and CSS classes as proposed by
[Bootstrap's style guide](https://getbootstrap.com/docs/5.1/forms/overview/):

![Address Form](readmeimg/bootstrap-address.png)

Or if rendered with alternative CSS classes:

```html
{% load formsetify %}
{% render_form form "bootstrap" field_css_classes="row mb-3" label_css_classes="col-sm-3" control_css_classes="col-sm-9" %}
```

![Address Form (horizontal)](readmeimg/bootstrap-address-horizontal.png)


Or if rendered with the Tailwind renderer:

```html
{% load formsetify %}
{% render_form form "tailwind" %}
```

![Address Form (Tailwind CSS)](readmeimg/tailwind-address.png)

**django-formset** provides form renderers for all major CSS frameworks, such as
[Bootstrap 5](https://getbootstrap.com/docs/5.1/forms/overview/),
[Bulma](https://bulma.io/documentation/form/general/),
[Foundation 6](https://get.foundation/sites/docs/forms.html),
[Tailwind](https://tailwindcss.com/) and [UIkit](https://getuikit.com/).


### Multiple Input Widgets

Furthermore, it can render all widgets provided by Django (except Geospacials). This includes
[multiple checkboxes](https://docs.djangoproject.com/en/stable/ref/forms/widgets/#checkboxselectmultiple)
and radio selects, even with multiple option groups:

![Multiple Inputs](readmeimg/bootstrap-multiple-input.png)


### File Uploading Widget

Uploading files is performed asynchronously, separating the payload upload from its form submission.
It provides a drag-and-drop widget plus a file select button. This allows to preview uploaded files
before form submission. It also make the submission much faster, because the file is already in a
temporary location on the server.

Empty file upload          | Pending file upload
:-------------------------:|:-------------------------:
![](readmeimg/bootstrap-upload-empty.png)|![](readmeimg/bootstrap-upload.png)


### Alternatives for `<select>` and `<select multiple>` Widgets

The default HTML `<select>` widget can be replaced by counterpart with autocompletion. No extra
endpoint is required, because that's handled by the same Django view controlling the form.

The default HTML `<select multiple="multiple">` widget can be replaced by two different widgets, one
which keeps the selected options inlined, and one which keeps them inside a "select-from" and a
"selected option" field.


## How does it work?

`<django-formset>` is a [Webcomponent](https://developer.mozilla.org/en-US/docs/Web/Web_Components)
to wrap one or more Django Forms. This webcomponent is installed together with the Django app
**django-formset**.


## Documentation and Demo

Reference documentation can be found on [Read The Docs](https://django-formset.readthedocs.io/en/latest/index.html).

A [demo](https://django-formset.fly.dev/) showing all combinations of fields.


## Usage

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

when rendering to HTML and using the
[Bootstrap 5 framework](https://getbootstrap.com/docs/5.0/getting-started/introduction/), we wrap
that Form into the special Webcomponent `<django-formset ...>`:

```html
{% load static formsetify %}
<html>
  <head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script type="module" src="{% static 'formset/js/django-formset.min.js' %}"></script>
  </head>
  <body>
    <!-- other stuff -->
    <django-formset endpoint="{{ request.path }}">
      {% render_form form "bootstrap" field_classes="mb-2" %}
      <button type="button" click="disable -> submit -> proceed !~ scrollToError" class="btn">Submit</button>
    </django-formset>
    <!-- other stuff -->
  </body>
</html>
```

in our `urls.py` we now wire everything together:

```python
from django.urls import path
from formset.views import FormView

from .myforms import SubscribeForm


urlpatterns = [
    ...
    path('subscribe', FormView.as_view(
        form_class=SubscribeForm,
        template_name='my-subscribe-form.html',
        success_url='/success',
    )),
    ...
]
```

This renders `SubscribeForm` with a much better User Experience. We get immediate feedback if input
entered into a field is not valid. Moreover, when this form is submitted but rejected by the
server-side validation checker, errors are shown immediatly and without reloading the page. Only on
success, a new page is loaded (or another alternative action is performed).


## Motivation

Instead of using a `<form>`-tag and include all its fields, here we wrap the complete form inside
the special Webcomponent `<django-formset>`. This allows us to communicate via Ajax with our Django
view, using the named endpoint. This means, that we can wrap multiple `<form>`-elements into our
Formset. It also means, that we now can place the Submit `<button>`-element outside of the
`<form>`-element. By doing so, we can decouple the Form's business-logic from its technical
constraint, of transferring a group of fields from and to the server. 

When designing this library, the main goal was to keep the programming interface a near as possible
to the way Django handles Forms, Models and Views.


## Some Highlights

* Before submitting, our Form is prevalidated by the browser, using the constraints we defined for
  each Django Field.
* The Form's data is sent by an Ajax request, preventing a full page reload. This gives a much
  better user experience.
* Server side validation errors are sent back to the browser, and rendered near the offending
  Form Field.
* Non-field validation errors are renderer together with the form.
* CSRF-tokens are handled through a HTTP-Header, hence there is no need to add a hidden input field
  to each form.
* Forms can be rendered for different CSS frameworks using their specific style-guides for arranging
  HTML. Currently **django-formset** includes renderers for:

  * [Bootstrap 5](https://getbootstrap.com/docs/5.0/forms/overview/),
  * [Bulma](https://bulma.io/documentation/form/general/),
  * [Foundation 6](https://get.foundation/sites/docs/forms.html),
  * [Tailwind](https://tailwindcss.com/) [^1]
  * [UIKit](https://getuikit.com/docs/form)

  It usually takes about 50 lines of code to create a renderer and most widgets can even be rendered
  using the default template as provided by Django. 
* It's JavaScript-framework agnostic. No external JavaScript dependencies are required. The client
  part is written in pure TypeScript and compiles to a single, portable JS-file.
* Support for all standard widgets Django currently offers. This also includes radio buttons and
  multiple checkboxes with options.
* File uploads are handled asynchronously. When the user opens the file dialog or drags a file into
  the form, this file then is uploaded immediately to a temporary folder on the server. On successful
  file upload, a unique signed handle is returned together with a thumbnail of that file. On form
  submission, this handle then is used to access that file and move it to its final destination.
  No extra endpoint is required for this feature.
* Select boxes with too many entries, can be filtered by the server using a search query. No extra
  endpoint is required for this feature.
* Radio buttons and multiple checkboxes with only a few fields can be rendered inlined rather than
  beneath each other.
* The Submit buttons can be configured as a chain of actions. It for instance is possible to disable
  the button before submission. It also is possible to change the CSS depending on success or
  failure, add delays and specify the further proceedings. This for instance allows to specify the
  success page as a HTML link, rather than having it to hard-code inside the Django View.
* A Formset can group multiple Forms into a collection. On submission, this collection then is
  sent to the server as a group a separate entities. After all Forms have been validated, the
  submitted data is provided as a nested Python dictionary.
* Such a Form-Collection can be declared to have many Form entities of the same kind. This allows to
  create siblings of Forms, similar the Django's Admin Inline Forms. However, each of these siblings
  can contain other Form-Collections, which themselves can also be declared as siblings. This list
  of siblings can be extended or reduced using one "Add" and multiple "Remove" buttons.
* By using the special attributes `show-if="condition"`, `hide-if="condition"` or
  `disable-if="condition"` on input fields or fieldsets, one can hide or disable these marked
  fields. This `condition` can evaluate all field values of the current Formset by a Boolean
  expression.

[^1]: Tailwind is special here, since it doesn't include purpose-built form control classes out of
      the box. Instead **django-formset** offers an opinionated set of CSS classes suitable for
      Tailwind.


## Running the Demo

Make sure you have a recent version of Python and npm.

To get a first impression of **django-formset**, run the demo site.

```shell
git clone https://github.com/jrief/django-formset.git
cd django-formset
python -m venv .venv
source .venv/bin/activate
pip install Django
pip install -r testapp/requirements.txt
pip install --no-deps -e .
npm install --also=dev
npm run tag-attributes
npm run tailwindcss
npm run build
testapp/manage.py migrate
testapp/manage.py runserver
```

Open http://localhost:8000/ in your browser. There is a link for each of the supported CSS
frameworks. For each of them, there is a long list of forms for all kind of purposes.


### Running the tests

Since there is a lot of interaction between the browser and the server, the client is tested using
[pytest](https://pytest-django.readthedocs.io/en/latest/) together with
[Playwright](https://playwright.dev/python/docs/intro/) in order to run end-to-end tests.


```shell
playwright install
```

Then run the testsuite

```shell
pytest testapp
```
