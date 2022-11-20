.. _buttons:

======================
Submit Button Controls
======================

In HTML each form must be submitted through a user defined action. This normally is done using
either an input field, or a button with type submit. This ``<button type="submit">Submit</button>``
or ``<input type="submit" value="Submit">`` must be placed inside the ``<form>...</form>``-element. 

**django-formset** has a different approach: Submit buttons shall be able to do *much more* than
just triggering an event, which then proceeds with submitting its form content to the server.
Instead, a button when clicked, can perform a whole chain of actions. This allows us to trigger more
than one event, whenever a user clicks on a button.

All controlling buttons must be placed inside the ``<django-formset>``-element. A typically submit
button therefore may look like

.. code-block:: django

	<django-formset …>
	  <!-- some forms with fields -->
	  …
	  <button click="disable -> submit -> proceed !~ scrollToError">Submit</button>
	</django-formset>


Action Queues
=============

What we see here are 4 actions: ``disable``, ``submit``, ``proceed`` and ``scrollToError``. Let's
explain their functionality:

* In ``disable``, the button disables itself. This is useful to prevent double submissions and
  should be used whenever possible.
* In ``submit``, the content of the form(s) inside the ``<django-formset>`` is submitted to the
  server through the given endpoint. This function can take extra values which are submitted along
  with the form data. If for example we use ``submit({foo: "bar"})`` then that extra submit data
  is available in our ``FormView`` instance connected to the given endpoint. That extra submitted
  data then can be accessed by calling ``self.get_extra_data()``. 
* If the submission was successful, ``proceed`` tells the client what to do next. If called without
  arguments, the default is to load the page given by the ``success_url`` provided by our Django
  view handling the request. If instead we use ``proceed("/path/to/success/page")``, that page is
  loaded on successful form submission. This allows web designers to specify that URL like a link,
  rather than having to rely on a response from the server.

A submission which did not validate on the server is considered as failed and the response status
code is 422, rather than 200. This is where the ``!~`` comes into play. It acts similar to a
catch-statement and everything after that symbol is executed on submission failure.

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
  be used on a separate button which explicitly is labeled to reset the form.
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
* ``emit("event name")`` emit a named event to the DOM.
* ``intercept`` intercepts the response object after submission and prints it onto the console. This
  is only useful for debugging purposes.
* ``clearErrors`` clears all error annotations from a previously failed form validation.
* ``noop`` does nothing and can be used as a placeholder.


By combining these button actions, we gain a huge set of possibilities to improve the user
experience. If for instance, form processing takes more than say one second, we shall somehow
signal to the user that the submission might take some time. This is where the ``spinner`` action
renders a spinning wheel. After a successful submission, we might want to signalize to the user that
everything is okay, before proceeding to the next page without notification. This is where the
``okay`` action displays an animated tick. In case of an unsuccessful submission attempt, we might
want to signalize to the user that it failed. This is where the ``bummer`` action displays an
animated failure.

This is an example of a ``click`` action on a button for a form requiring some processing time:

.. code-block:: django

	<button type="button" click="disable -> spinner -> submit -> okay(1500) -> proceed !~ enable -> bummer(9999)">
		Submit
		<span class="dj-button-decorator"><img class="dj-icon" src="/path/to/icon" /></span>
	</button>

.. image:: _static/submit-success.gif
  :width: 145
  :alt: Submit Button (success)

Here we delay the okay tick by 1.5 seconds before proceeding to the next page.

.. image:: _static/submit-failure.gif
  :width: 145
  :alt: Submit Button (failure)

In case of failure, we render the bummer symbol for 10 seconds before resetting it to the default.


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
	      <button type="button" click="submit({published: false}) -> proceed">
	        Unpublish Post
	      </button>
	    {% else %}
	      <button type="button" click="submit({published: true}) -> proceed">
	        Publish Post
	      </button>
	    {% endif %}
	      <button type="button" click="proceed('{{ editview_url }}')">
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
