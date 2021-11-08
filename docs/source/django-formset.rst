.. _django-formset:

Webcomponent ``<django-formset>``
=================================

When a form is rendered using a Django template, we must wrap it inside the webcomponent
``<django-formset>``. This component then takes care of the client-part, such as the form
validation, submission, error handling and many other features.

A mandatory attribute of each web component ``<django-formset>`` is its ``endpoint``. This is the
URL pointing onto a Django view and is where the client-part communicate with the server.
Typically that endpoint is connected to a :class:`formset.views.FormView`. We can either
inherit from that class and specialize into our own view class

.. code-block:: python

	from formset.views import FormView
	
	class RegisterPersonFormView(FormView):
	    template_name = 'path/to/register-person-form.html'
	    form_class = RegisterPersonForm
	    success_url = '/success'

or use that class directly in ``urls.py`` while defining the routing:

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

	<django-formset endpoint="{{ request.path }}" force-submission="..." withhold-messages="...">
	  ...
	</django-formset>

We can do this, because the endpoint is located on the same URL as the view rendering the form.

An optional attribute to our web component ``<django-formset>`` is ``force-submission``. By setting
this to ``true``, we can force a submission to the server, even if the form did not validate on the
client side. This attribute defaults to ``false``, meaning that forms, which did not validate
can not be submitted to the server.

Another optional attribute to our web component ``<django-formset>`` is ``withhold-messages``. By
setting this to ``true``, we can withhold validation error messages until the user submits the form.
This attribute defaults to ``false``, meaning that a field validation error message is shown
immediatly after the user blurs a field containig invalid data.

Non-field errors need more logic and are always computed on the server.
