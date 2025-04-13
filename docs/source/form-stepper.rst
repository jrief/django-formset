.. _form-stepper:

============
Form Stepper
============

.. versionadded:: 1.7

Whenever we need a user to fill multiple forms, it sometimes is convenient to break them up into
multiple steps. This keeps the number of fields per form low and makes the form filling process
less overwhelming. In addition, it allows to validate each form separately and to display the
display progress through a sequence by breaking it up into multiple logical and numbered steps.

For this purpose, **django-formset** offers the special stepper collection class
:class:`formset.stepper.StepperCollection`. It can be used as a direct replacement for
:ref:`collections` with a slightly different behaviour.

Just as with Form Collections, the Stepper Collection is a collection of forms or other collections.
However, only one of those forms is displayed at a time. Typically, a user can navigate through
those forms sequentially and only if the currently visible form is filled with valid data, the user
can proceed to the next form. This means that we usually prevalidate each form on each step.

Here as an example of a checkout form, as often found in e-commerce sites:

.. django-view:: stepper_form
	:caption: checkout.py

	from django.forms.fields import CharField, RegexField
	from django.forms.forms import Form

	from formset.formfields import Activator
	from formset.stepper import StepperCollection
	from formset.widgets import Button

	class ContactForm(Form):
	    step_label = "Contact"
	    induce_activate = 'shipping.previous:active'
	
	    full_name = CharField()
	    next = Activator(
	        label="Next",
	        widget=Button(action='submitPartial -> activate("apply")')
	    )

	class ShippingForm(Form):
	    step_label = "Shipping"
	    induce_activate = 'contact.next:active || payment.previous:active'
	
	    address = CharField(
	        label="Address",
	    )
	    previous = Activator(
	        label="Previous",
	        widget=Button(action='activate("apply")')
	    )
	    next = Activator(
	        label="Next",
	        widget=Button(action='submitPartial -> activate("apply")')
	    )
	
	class PaymentForm(Form):
	    step_label = "Payment"
	    induce_activate = 'shipping.next:active'
	
	    card_number = RegexField(
	        r'^(\d{16}|\d{4}\s\d{4}\s\d{4}\s\d{4})$',
	        label="Card Number",
	    )
	    previous = Activator(
	        label="Previous",
	        widget=Button(action='activate("apply")')
	    )
	    submit = Activator(
	        label="Submit",
	        widget=Button(action='submit -> intercept("#submit-data") !~ intercept("#submit-data")')
	    )

	class CheckoutCollection(StepperCollection):
	    legend = "Checkout your Order"
	    contact = ContactForm()
	    shipping = ShippingForm()
	    payment = PaymentForm()
	

.. django-view:: checkout_view
	:view-function: CheckoutView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'submit'}, collection_kwargs={'auto_id': 'co_id_%s', 'renderer': FormRenderer(field_css_classes='mb-3')})
	:hide-code:

	from formset.views import FormCollectionView

	class CheckoutView(FormCollectionView):
	    collection_class = CheckoutCollection
	    template_name = "collection-no-button.html"
	    success_url = "/success"

For simplicity, the above example uses just one field per form. A real world application, would of
course use many more fields for a checkout. Let's explain the above code step by step:

The class ``CheckoutCollection`` contains three forms, each representing a step in the checkout.
Each step is represented by a form class, which is derived from Django's ``Form`` class. However,
such a form class is extended by a few additional attributes:

* ``step_label``: This is a human readable label, which is displayed in the stepper navigation.
* ``induce_activate``: This is a JavaScript expression, which controls the activation of the form.
  It is evaluated by looking for actions on the referring buttons. The form ``ContactForm`` uses
  the action ``shipping.previous:active``. This means that the form is activated whenever the button
  ``previous`` on the form ``ShippingForm`` is clicked. The form ``ShippingForm`` uses the action
  ``contact.next:active || payment.previous:active``. This means that the form is activated whenever
  the button ``next`` on the form ``ContactForm`` is clicked or the button ``previous`` on the form
  ``PaymentForm`` is clicked. The same action rule applies to the form ``PaymentForm``.

In the first two forms there are :ref:`activators` labeled "Next" with the action ``submitPartial ->
activate("apply")``. This means that the current form is partially submitted to the server and
validated there. If the latter succeeds the button is considered as activated and the next form is
displayed. If this partial submission fails, the invalid fields are highlighted but otherwise
nothing happens.

The buttons labeled "Previous" have no action ``submitPartial``, because we want to allow users to
return back to their previous form, regardless of its validity state.

The last form contains an activator labeled "Submit" with the action ``submit -> intercept("…")
!~ intercept("…")``. By clicking on this button, the payload of this complete collection is sent to
the server and processed there as usual.

.. note:: In this example the use of the ``intercept`` actions is just for debugging purpose. It
	is used to show the submitted content in this application. A real world application would not
	implement this action. 

The stepper navigation is rendered as a list of bullets. These bullets are clickable and allow the
user to jump to any step as long as the previous steps are valid. The current step is highlighted
and the steps which are not yet reached are displayed in a disabled state.
