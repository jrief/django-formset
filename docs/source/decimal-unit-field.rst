.. _decimal-unit-field:

==================
Decimal Unit Field
==================

Django offers three built-in form fields to enter numeric values, namely DecimalField_, FloatField_
and IntegerField_ . When rendered as HTML, their element usually boils down to something like

.. code-block:: text

	<input type="number" name="…" value="…" …>

This `HTML input element`_ is a good choice for entering numbers, but it has some limitations:

* Locale-specific number formatting is not enforced; the decimal separator can be ``.`` or ``,``.
* It allows non-numeric input via copy-paste or browser autofill in some browsers.
* It does not support units, for example €, $, £, ¥, kg, %, etc. – only plain numbers.
* Validation and step increments may behave inconsistently across browsers.
* It does not handle very large or very small numbers well due to floating-point precision.
* Custom formatting (like thousand separators) is not supported.
* Accessibility and mobile keyboard support can vary between browsers and devices.

To improve the user experience, **django-formset** provides the custom widget
:class:`formset.widgets.DecimalUnitInput` to enter numbers in a well formatted way. This widget is
designed to add thousand separators, handle the locale-specific decimal separator properly and add a
prefix to the input field. It can be used as a direct replacement for the built-in Django widget
NumberInput_ and shall be used with one of the mentioned Django form fields.

.. _DecimalField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#decimalfield
.. _FloatField:  https://docs.djangoproject.com/en/stable/ref/forms/fields/#floatfield
.. _IntegerField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#integerfield
.. _NumberInput: https://docs.djangoproject.com/en/stable/ref/forms/widgets/#numberinput
.. _HTML input element: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/number


Example
=======

Say that we have a form to enter the price of a product, which is a decimal number with a currency
unit. The form field is defined as follows:

.. django-view:: decimal_unit_form
	:caption: form.py
	:emphasize-lines: 7

	from django.forms import fields, forms
	from formset.widgets import DecimalUnitInput

	class PriceForm(forms.Form):
	    price = fields.DecimalField(
	        label="Price",
	        widget=DecimalUnitInput(prefix="€", fixed_decimal_places=True),
	        min_value=0,
	        decimal_places=2,
	        max_digits=10,
	        step_size=0.01,  # allows multiples of 1 cent
	    )

.. django-view:: decimal_unit_view
	:view-function: PriceView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'proce-result'}, form_kwargs={'auto_id': 'pf_id_%s'})
	:hide-code:

	from formset.views import FormView

	class PriceView(FormView):
	    form_class = PriceForm
	    template_name = "form.html"
	    success_url = "/success"

What we see here is an input field accepting a decimal number for a price tag. By replacing the
default widget against the custom widget :class:`formset.widgets.DecimalUnitInput`, we can improve
the user experience significantly. This widget will then render a replacement (using
``contenteditable="true"``) for the input field.

The widget ``DecimalUnitInput`` accepts three optional parameters, ``prefix``, ``suffix`` and
``fixed_decimal_places``. The ``prefix`` is a string that will be prepended to the input field,
while the ``suffix`` is a string that will be appended to the input field. In this example, we use
the Euro sign "``€``" as a prefix to indicate that the price is in Euro. The parameter
``fixed_decimal_places`` is a Boolean value and used to pad the decimal fraction with ``0``-s. If
unset or ``False``, the widget will not enforce a fixed number of decimal places, and just allow the
maximum as specified by ``decimal_places`` in the form field.

This widget adopts all the constraints from the underlying form field, such as minimum and maximum
values, number of decimal places, and step size. The widget will automatically format the number, so
that the decimal separator (``.`` or ``,``) always corresponds to the locale settings of the user.

As the thousands separator, **django-formset** uses a narrow spaces instead of commas or dots, which
is a good compromise between readability and conciseness. Those narrow spaces are not navigable,
meaning that the caret skips them while moving left or right.

With no or a negative ``minimum_value``, the widget allows to enter negative numbers. Otherwise the
minus sign is not allowed.

If ``decimal_places`` is set to 0, the widget will not allow to enter a decimal number at all, not
even the decimal separator. With ``decimal_places`` greater than zero, the entered number is rounded
to its nearest possible value. If for instance you paste the value ``1234.567`` into the above input
field, it will be rounded to "1234.57".

The ``max_digits`` attribute is used to specify the maximum number of digits that can be entered.
This includes both the integer and decimal parts of the number. If the entered number exceeds this
limit, the widget will strip the excess digits from the right side.

The ``step_size`` attribute is used to specify the step size for the input field. This is useful for
example when entering prices, where the step size is usually 0.01 (1 cent). Entered values always
must be multiples of the given step size. If the user uses the up or down arrow keys on such a
focused input field, the value will be incremented or decremented by the given step size.
