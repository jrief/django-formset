.. _buttons:

======================
Submit Button Controls
======================

In HTML each form must be submitted through a user defined action. Normally it's done either using
an input field, or a button with type submit. This ``<button type="submit">Submit</button>``
or ``<input type="submit" value="Submit">`` must be placed inside the ``<form>...</form>``-element. 

**django-formset** has a different approach: Submit buttons shall be able to do *much more* than
just triggering *the* event, which then proceeds with submitting its form content to the server.
Instead, a button when clicked, can perform a whole chain of actions. This allows us to trigger more
than one event, whenever a user clicks on a button.

All controlling buttons must be placed inside the ``<django-formset>``-element. A typically submit
button therefore may look like

.. code-block:: django
	:emphasize-lines: 4

	<django-formset …>
	  <!-- some forms with fields -->
	  …
	  <button df-click="disable -> submit -> proceed !~ scrollToError">Submit</button>
	</django-formset>


.. _action-queues:

Action Queues
=============

Here we recognize four actions: ``disable``, ``submit``, ``proceed`` and ``scrollToError``. Let's
explain their functionality:

* In ``disable``, the button disables itself. This is useful to prevent double submissions and
  should be used whenever possible.
* In ``submit``, the content of the form(s) inside the ``<django-formset>`` is submitted to the
  server through the given endpoint. This function can take extra values which are submitted along
  with the form data. If for example we use ``submit({foo: "bar"})`` then that extra data is
  submitted along with the form's payload and will be available to our ``FormView`` instance, which
  is connected to the given endpoint. From inside that ``FormView`` instance the submitted extra
  data can then be accessed by calling ``self.get_extra_data()``. 
* If the submission was successful, ``proceed`` tells the client what to do next. If called without
  arguments, the default is to load the page given by the ``success_url`` provided by our Django
  view handling the request. If instead we use ``proceed("/path/to/success/page")``, that page is
  loaded on successful form submission. This allows web designers to specify that URL like a link,
  rather than having to rely on a response from the server.

A submission which did not validate on the server is considered as failed and the response status
code is 422, rather than 200. This is where the ``!~``-operator comes into play. It acts similar to
a catch-statement and everything after that symbol is executed on submission failure.

.. note:: According to `RFC4918 Section 12.1`_, a status code of 422 can be used if a request body
	contains well-formed (i.e., syntactically correct), but semantically erroneous, instructions.
	Even though the cited RFC applies to XML, invalid form data submitted via JSON can as well be
	interpreted as “semantically erroneous”.

.. _RFC4918 Section 12.1: https://www.rfc-editor.org/rfc/rfc4918#section-11.2

* In ``scrollToError`` the browser scrolls to the first field, which was marked to contain invalid
  input data.

The above 4 functions are the most useful ones, but there are many more functions to be used
as queued actions for buttons in **django-formset**:

* ``enable`` is used to re-enable a previously disabled button. By default, every button is put into
  the state just before having clicked on it, regardless if the submission was successful or not.
  Therefore this action is rarely of usage.
* ``reset`` is used to reset all form fields to their state when loading the form. It usually should
  be used on a separate button which explicitly is labeled to *reset* the form.
* ``reload`` this is used to reload the page. Useful to reload the form after a successful
  submission, for instance in buttons labeled “*Save and continue editing*”.
* ``delay(1000)`` delays all further actions by one second. This sometimes can be useful to add an
  extra delay (in milliseconds) during the submission.
* ``spinner`` if the button contains a decorator element, ie. a child with
  ``class="dj-button-decorator"``, then that element is replaced by a rotating spinner symbol.
  Useful to give feedback before time consuming submissions. 
* ``okay`` if the button contains a decorator element, ie. a child with
  ``class="dj-button-decorator"``, then that element is replaced by an animated okay tick. Useful to
  give feedback after a successful form submission. This action takes an optional delay argument in
  milliseconds, in order to visualize the animation before proceeding. 
* ``bummer`` if the button contains a decorator element, ie. a child with
  ``class="dj-button-decorator"``, then that element is replaced by an animated bummer symbol.
  Useful to give feedback after a failed form submission. This action takes an optional delay
  argument in milliseconds, in order to visualize the animation before proceeding.
* ``addClass("foo")`` adds the CSS class "foo" to the button class. After submission, this class is
  automatically removed from the class.
* ``removeClass("foo")`` removes the CSS class "foo" to the button class.
* ``toggleClass("foo")`` toggles the CSS class "foo" on the button class.
* ``confirm("A question?")`` opens a confirmation popup with the given message string together with
  a "Cancel" and an "OK" button. If the user clicks on "Cancel", the action chain is interrupted.
  This action typically precedes the ``submit``-action to prompt the user for confirmation.
* ``alertOnError`` typically is added after the ``!~`` operator. In case the form submission
  generated an non-form-validation error, for instance "permission denied", this error is shown in
  an alert box. 
* ``setFieldValue(path.to.target, source_value)`` sets a value to the field specified by the target
  path. The source value can be a string, number, boolean or the path to another source field. In
  the latter case that value is transferred to the target field.
  By prefixing the source value with a ``^`` caret, the value is taken from a response object
  fetched by a previous request.
* ``emit("event name")`` emit a named event to the DOM.
* ``clearErrors`` clears all error annotations from a previously failed form validation.
* ``activate`` activates the button to be intercepted by another component, for instance in
  :ref:`dialog-forms`.
* ``activate("command")`` The command is passed as an argument to the interceptor.
* ``noop`` does nothing and can be used as a placeholder.
* ``intercept`` intercepts the response object after submission and prints it onto the browser
  console. This is only useful for debugging purposes.
* ``intercept("<dom-selector>")`` prints the intercepted submission to a HTML element as specified
  by the ``<dom-selector>``. This documentation makes heavy use of that feature.

By combining these button actions, we gain a huge set of possibilities to greatly improve the user
experience. If for instance, form processing takes more than say one second, we shall somehow
signal to the user that the submission might take some time. This is where the ``spinner`` action
renders a spinning wheel. After a successful submission, we might want to signalize to the user that
everything is okay, before proceeding to the next page without notification. This is where the
``okay`` action displays an animated tick. In case of an unsuccessful submission attempt, we might
want to signalize to the user that it failed. This is where the ``bummer`` action displays an
animated failure.

This is an example of a ``df-click`` action on a button for a form requiring some processing time:

.. code-block:: html

	<button type="button" df-click="disable -> spinner -> submit -> okay(1500) -> proceed !~ enable -> bummer(5000)">
	    Submit
	    <span class="dj-button-decorator"><img class="dj-icon" src="/path/to/icon" /></span>
	</button>

.. django-view:: button_action
	:view-function: ButtonActionView.as_view(extra_context={'button_actions': 'disable -> spinner -> submit -> okay(1500) -> reload !~ enable -> bummer(5000)'})
	:hide-code:

	from time import sleep
	from django.core.exceptions import ValidationError
	from django.forms import fields, forms, widgets
	from formset.views import FormView 
	
	class EmptyForm(forms.Form):
	    valid = fields.BooleanField(
	        label="Valid",
	        required=False,
	        help_text="Check to make this form valid",
	    )

	    def clean_valid(self):
	        sleep(1.5)  # emulate heavy form processing
	        if not self.cleaned_data.get('valid'):
	            raise ValidationError("This form is not valid.")
	        return True

	class ButtonActionView(FormView):
	    form_class = EmptyForm
	    template_name = "button-action.html"
	    success_url = "/success"

Here we use the checkbox to emulate a successful and a failing server side form validation.

.. note:: The view behind this action, emulates heavy form processing by waiting for 1.5 seconds.
	After the form was successfully submitted, the okay tick waits for another 1.5 seconds before
	proceeding. Since this action view has no associated success page, the current page is just
	reloaded.
	
	In case of failure, we render the bummer symbol for 5 seconds before resetting it to the
	default.


Ternary Operator
----------------

The `ternary operator`_ is a tool to conditionally execute different action queues. This allows us
to  use one action queue if a certain condition is met, otherwise another action queue is executed.
The syntax is ``condition ? action1 -> action2 !~ failed : action3 -> action4``. Remember that the
``!~`` operator is used to catch failed submissions. It has a higher precedence over the ternary
operator. As ``condition`` we typically use the value of a field in the current form or collections
of thereof.

.. _ternary operator: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Conditional_operator


Buttons without a Form
======================

Sometimes we just need to send a certain event to the server, without having to fill out a form.
Consider a blog application, where the blog post model contains a boolean field named ``published``.
We want our application to show a preview page of our blog post, so after editing and submitting the
main content, the detail page of that post shall appear. There we add a button to publish the page.
With **django-formset**, we can reuse the same edit view. 

This is the final part of the template rendering the detail view of our blog post:

.. code-block:: django

	{# the detail view of our blog post #}
	{% if is_owner %}
	  <django-formset endpoint="{{ editview_url }}" csrf-token="{{ csrf_token }}">
	    {# no <form> element is rendered here, because single field `published` is handled through action buttons #}
	    {% if post.published %}
	      <button type="button" df-click="submit({published: false}) -> proceed">
	        Unpublish Post
	      </button>
	    {% else %}
	      <button type="button" df-click="submit({published: true}) -> proceed">
	        Publish Post
	      </button>
	    {% endif %}
	      <button type="button" df-click="proceed('{{ editview_url }}')">
	        Change Post
	      </button>
	  </django-formset>
	{% endif %}

Here ``editview_url`` points onto the view used to edit the blog post:

.. code-block:: python
	:caption: edit_view.py

	class EditBlogPostView(LoginRequiredMixin, FormViewMixin, UpdateView):
	    model = BlogPost
	    form_class = BlogPostForm
	    template_name = 'edit-blog-post.html'
	
	    def post(self, request, *args, **kwargs):
	        if extra_data := self.get_extra_data():
	            if 'published' in extra_data:
	                instance = self.get_object()
	                instance.published = extra_data['published']
	                instance.save(update_fields=['published'])
	                return JsonResponse({'success_url': self.get_success_url()})
	        return super().post(request, *args, **kwargs)

	    # other methods

What we do here is to bypass form validation if we find out that besides "form data", some
``extra_data`` is submitted. This data originates from the ``submit({published: true/false})``
buttons from above. 

This neat trick allows us to reuse the edit view class for a similar purpose.

.. _auto-disable_buttons: 

Auto-Disable Buttons
====================

By adding the Boolean attribute ``auto-disable`` to any ``<button …>``, that button element remains
disabled until the complete formset contains valid data. This can be used to prevent users from
submitting forms with missing fields or fields containing invalid data.

From a usability consideration, this setting should only be used, if the form contains very few
fields and these fields must always be visible together with that button. To the user it then must
be immediately clear that this button is disabled, *because* some nearby fields are missing. If that
can't be guaranteed, it is better to let the user submit a form containing invalid data and then
scroll to the first field, which doesn't.
