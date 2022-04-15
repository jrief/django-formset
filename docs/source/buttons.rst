.. _buttons:

======================
Submit Button Controls
======================

In HTML each form must be submitted through a user defined action. This usually is done using either
an input field, or a button with type submit. This button must be placed inside the form. 

**django-formset** has a different approach. Submit buttons shall be able to do much more than just
triggering an event, which then proceeds with an action on the form. They can perform a whole chain
of actions when clicked. All controlling buttons must be placed inside the
``<django-formset>``-element. A typically submit button may look like

.. code-block:: html

	<button click="disable -> submit -> proceed !~ scrollToError">Submit</button>

What we see here are 4 actions, ``disable``, ``submit``, ``proceed`` and ``scrollToError``. Let's go
into details: 

* In ``disable``, the button disables itself. This is useful to prevent double submissions and
  should be used whenever possible.
* In ``submit``, the content of the form(s) inside the ``<django-formset>`` is submitted to the
  server through the given endpoint. This function can take extra values which are submitted along
  with with the form data, for example using ``submit({foo: "bar"})``. That extra submit data then
  is available in the ``FormView`` object connected to the endpoint, by callig ``get_extra_data()``. 
* If the submission was successful, ``proceed`` tells the client what to do next. If called without
  parameter, the default is to load the page given by the ``success_url`` in the Django View
  handling the request. If instead we use ``proceed("/path/to/success/page")``, that page is loaded
  on successful form submission. This allows web designers to specify that URL like a link, rather
  than having to rely on the server's response.

An submission which did not validate on the server is considered as failed and the response status
code is 422, rather than 200. This is where the ``!~`` comes into play. This acts as a
catch-statement and everything afterwards is executed on submission failure.

* In ``scrollToError`` the browser scrolls to the first field, which was marked to contain invalid
  input data.

The above 4 functions are the most useful ones, but there are many more functions to be used
together with **django-formset**:

* ``enable`` is used to re-enable a previously disabled button. By default, every button is put into
  the state just before having clicked on it, regardless if the submission was successful or not.
  Therefore this action is rarely of usage.
* ``reset`` is used to reset all form fields to their state when loading the form. It usually should
  be used on a separate button which explicitly is named to reset the form.
* ``delay(1000)`` delays all further actions by one second. This sometimes can be useful to add an
  extra delay (in microseconds) during the submission.
* ``addClass("foo")`` adds the CSS class "foo" to the button class. After submission, this class is
  automatically removed from the class.
* ``removeClass("foo")`` removes the CSS class "foo" to the button class.
* ``toggleClass("foo")`` toggles the CSS class "foo" on the button class.
* ``emit("event name")`` emit a named event to the DOM.
* ``intercept`` intercepts the response object after submission and prints it onto the console. This
  is only useful for debugging purpose.
* ``noop`` does nothing and can be used as a placeholder.
