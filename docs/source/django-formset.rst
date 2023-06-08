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
	
	class PersonFormView(FormView):
	    template_name = "form.html"
	    form_class = RegisterPersonForm
	    success_url = "/success"

or use the class ``FormView`` directly in ``urls.py`` while defining the routing:

.. code-block:: python

	urlpatterns = [
	    ...
	    path("person", FormView.as_view(
	        template_name="form.html",
	        form_class=RegisterPersonForm,
	        success_url = "/success",
	    )),
	    ...
	]

In this example, the endpoint would point onto ``/person``, but in order to make our form
rendering templates reusable, we'd rather write

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  ...
	</django-formset>

We can do this, because the endpoint is located on the same URL as the view rendering the form.

.. rubric:: CSRF token

Since the JavaScript implementing web component ``<django-formset>`` communicates with the server
using the `fetch function`_ , having a hidden input field containing the CSRF-token doesn't make
sense. Instead we pass that token value as an attribute to the web component ``<django-formset>``.
Since that value is available in the rendering context, we always add it as
``<django-formset csrf-token="{{ csrf_token }}">``.

.. _fetch function: https://developer.mozilla.org/en-US/docs/Web/API/fetch

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
``withhold-feedback="warnings success"``. More on this can be found in section
:ref:`withholding-feedback`.
