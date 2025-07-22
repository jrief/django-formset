.. _decimal-unit-field:

==================
Decimal Unit Field
==================

Django offers three built-in form fields to enter numbers, namely DecimalField_, FloatField_ and
IntegerField_ . When rendered as HTML, their element usually boils down to something like

.. code-block:: html

	<input type="number" name="…" value="…">

This `HTML element`_ is a good choice for entering numbers, but it has some limitations:

* It does not support locale-specific number formatting (e.g., decimal separator is always "``.``").
* It allows non-numeric input via copy-paste or browser autofill in some browsers.
* It does not support units, for example €, $, £, ¥, kg, %, etc. – only plain numbers.
* Validation and step increments may behave inconsistently across browsers.
* It does not handle very large or very small numbers well due to floating-point precision.
* Custom formatting (like thousand separators) is not supported.
* Accessibility and mobile keyboard support can vary between browsers and devices.

To improve the user experience, **django-formset** provides a custom widget
:class:`formset.widgets.DecimalUnitInput` to enter numbers in a well formatted way. This widget is
designed to add thousand separators, handle the locale-specific decimal separator properly and add a
prefix to the input field. It can be used as a direct replacement of the built-in Django widget
NumberInput_ and shall be used with one of the mentioned Django form fields.

.. _DecimalField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#decimalfield
.. _FloatField:  https://docs.djangoproject.com/en/stable/ref/forms/fields/#floatfield
.. _IntegerField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#integerfield
.. _NumberInput: https://docs.djangoproject.com/en/stable/ref/forms/widgets/#numberinput
.. _HTML element: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/number

Say that we have a form to enter the price of a product, which is a decimal number with a currency
unit. The form field is defined as follows:

.. django-view:: decimal_unit_form
	:caption: form.py

	from django.forms import fields, forms
	from formset.widgets import DecimalUnitInput

	class PriceForm(forms.Form):
	    price = fields.DecimalField(
	        label="Price",
	        widget=DecimalUnitInput(prefix="€"),
	        min_value=0,
	        decimal_places=2,
	        max_digits=10,
	        step_size=0.1,  # allows only multiples of 10 cents
	    )

.. django-view:: decimal_unit_view
	:view-function: PriceView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'proce-result'}, form_kwargs={'auto_id': 'pf_id_%s'})
	:hide-code:

	from formset.views import FormView

	class PriceView(FormView):
	    form_class = PriceForm
	    template_name = "form.html"
	    success_url = "/success"

What we see here is an input field accepting a decimal number for a price tag. By using the prefix
"€" we can inform the users of this form that the price is intended to be in Euro. This widget
adopts all the constraints from the underlying form field, such as minimum and maximum values,
number of decimal places, and step size. The widget will automatically format the number according
to the locale of the user, so that the decimal separator (``.`` or ``,``) is always correct. As the
thousands separator, **django-formset** uses a narrow spaces instead of commas or dots, which is a
good compromise between readability and exactness. Those narrow spaces are not navigable, meaning
that the caret skips them while moving left or right.
