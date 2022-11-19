.. _django-formset:

==================================
Web Component ``<django-formset>``
==================================

When a form is rendered using a Django template, we must wrap it inside the web component
``<django-formset>``. This component then takes care of the client-part, such as the form
validation, submission, error handling and many other features.

A mandatory attribute of each web component ``<django-formset>`` is its ``endpoint``. This is the
URL pointing onto a Django view and this is how the client-part communicates with the server.
Typically that endpoint is connected to a view inheriting from :class:`formset.views.FormView`. We
can either inherit from that class, specialize into our own view class and register it in the URL
router,

.. code-block:: python

	from formset.views import FormView
	
	class RegisterPersonFormView(FormView):
	    template_name = 'path/to/register-person-form.html'
	    form_class = RegisterPersonForm
	    success_url = '/success'

or use the class ``FormView`` directly in ``urls.py`` while defining the routing:

.. code-block:: python

	urlpatterns = [
	    ...
	    path('register-person', FormView.as_view(
	        template_name='path/to/register-person-form.html',
	        form_class=RegisterPersonForm,
	        success_url = '/success',
	    )),
	    ...
	]

In this example, the endpoint would point onto ``/register-person``, but in order to make our form
rendering templates reusable, we'd rather write

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  ...
	</django-formset>

We can do this, because the endpoint is located on the same URL as the view rendering the form.


.. rubric:: Enforcing Form Submission

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" force-submission csrf-token="{{ csrf_token }}">
	  ...
	</django-formset>

An optional attribute to this web component is ``force-submission``. By adding this attribute, we can
force a submission to the server, even if the form did not validate on the client side. The default
is to always validate all form fields on the client, and only if all of them pass, proceed with
the submission to the server.


.. rubric:: Withholding Feedback

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" withhold-feedback="..." csrf-token="{{ csrf_token }}">
	  ...
	</django-formset>

An optional attribute to this web component is ``withhold-feedback``. By setting this to
``messages``, ``errors``, ``warnings``, ``success``, or any combination of thereof, we can withhold
the feedback, which is shown immediately after the user types into a field or when a field loses
focus. When combining two or more "withhold feedback" values, separate them by spaces, for instance 
``withhold-feedback="warnings success"``.

Adding ``messages`` to ``withhold-feedback="..."`` means that the error message below the field
will not be rendered when the user blurs a field with invalid data. 

Adding ``errors`` to ``withhold-feedback="..."`` means that the border does not change color
(usually red) and the field does not show an alert symbol, when the user blurs a field with invalid
data.

Adding ``warning`` to ``withhold-feedback="..."`` means that the field does not show a warning
symbol (usually orange), when a field has focus, but its content does not contain valid data (yet).
If only attribute ``errors`` has been added to ``withhold-feedback="..."``, then the warning symbol
will remain even if the field loses focus.

Adding ``success`` to ``withhold-feedback="..."`` means, that the border does not change color
(usually green) and the field does not show a success symbol, when the user blurs a field with
valid data.

The attribute ``withhold-feedback="..."`` only has effect while editing the form fields. Whenever
the user clicks on the submit button of a form containing invalid data, then all fields which
did not validate, will show their error message together with an alert symbol and an alert border
(usually red).

Non-field errors need more validation logic and therefore are always determined on the server,
usually by the ``clean()``-method of the form class.
