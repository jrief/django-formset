.. _withholding-feedback:

====================
Withholding Feedback
====================

**django-formset** gives immediate feedback, as soon as a user starts typing into a field. While an
input field has focus, and the field is believed to have invalid data, an orange warning triangle
appears on the right. As soon as the field loses focus (blurs), the field is validated by the
client-side implementation. If its data does not validate, a red exclamation mark is shown and the
field's border is rendered in red. Additionally an error message is rendered below the field. On the
other hand, if the field data validates, a green tick is shown and the field's border is rendered in
green.

This default behavior is not always desired and can be configured to be less verbose.

Here is a simple form used to show how to withhold various feedback messages nearby the
offending fields. This is done by adding the attribute ``withhold-feedback="..."`` with one
or a combination of those values: ``messages``, ``errors``, ``warnings`` and/or ``success``.
These four values can be combined to create the desired feedback.

.. django-view:: person_view
	:view-function: PersonView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'person-result'}, form_kwargs={'auto_id': 'pf_id_%s'})
 
	from django.forms import fields, forms
	from formset.views import FormView
 
	class PersonForm(forms.Form):
	    last_name = fields.CharField(
	        label="Last name",
	        min_length=2,
	        max_length=50,
	        help_text="Please enter at least two characters",
	    )
	    first_name = fields.RegexField(
	        r'^[A-Z][ a-z\-]*$',
	        label="First name",
	        error_messages={'invalid': "A first name must start in upper case."},
	        help_text="Must start in upper case followed by one or more lowercase characters.",
	        max_length=50,
	    )
	
	    def clean(self):
	        cd = super().clean()
	        if (cd.get('first_name', '').lower().startswith("john")
	            and cd.get('last_name', '').lower().startswith("doe")):
	            raise ValidationError(
	                f"{cd['first_name']} {cd['last_name']} is persona non grata here!"
	            )
	        return cd

	class PersonView(FormView):
	    form_class = PersonForm
	    template_name = "form.html"
	    success_url = "/success"

This form behaves as the default. We now can change the feedback behavior by adding the special
argument ``withhold-feedback="…"`` to the directive ``<django-formset>``.


Withhold Validation Tick
========================

.. django-view:: person_view_wf_success
	:view-function: PersonView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'person-wf-success', 'withhold_feedback': 'success'}, form_kwargs={'auto_id': 'wfs_id_%s'})
	:hide-code:

In this example we use ``withhold-feedback="success"``. Whenever a form field with valid data loses
focus, the field border does not change to green and no tick is rendered on the right part of the
field.


Withhold Error Messages
=======================

.. django-view:: person_view_wf_messages
	:view-function: PersonView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'person-wf-messages', 'withhold_feedback': 'messages'}, form_kwargs={'auto_id': 'wfm_id_%s'})
	:hide-code:

In this example we use ``withhold-feedback="messages"`` to withhold the red error message. Whenever
a form field with invalid data loses focus, no message is rendered below that field. Note that this
only applies to client-side form validation. Whenever the server rejects a submitted form containing
invalid data, those messages are still rendered below those fields. 


Withhold Error Symbol
=====================

.. django-view:: person_view_wf_errors
	:view-function: PersonView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'person-wf-errors', 'withhold_feedback': 'errors'}, form_kwargs={'auto_id': 'wfe_id_%s'})
	:hide-code:

In this example we use ``withhold-feedback="errors"`` to withhold the red field border. Whenever
a form field with invalid data loses focus, no red encircled exclamation mark appears on the right
and the border color does not change to red. Note that this only applies to client-side form
validation. Whenever the server rejects a submitted form containing invalid data, those fields are
still rendered using the "error" feedback. 


Withhold Warning Symbol
=======================

.. django-view:: person_view_wf_warnings
	:view-function: PersonView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'person-wf-warnings', 'withhold_feedback': 'warnings'}, form_kwargs={'auto_id': 'wfw_id_%s'})
	:hide-code:

In this example we use ``withhold-feedback="warnings"`` to withhold the orange warning triangle.
Whenever a focused form field does not contain valid data (yet), no warning triangle is rendered
on the right side of that field. If attribute ``errors`` has been added to
``withhold-feedback="…"``, then this warning symbol will remain even if the field loses focus.


Server-Side Validation
======================

The attribute ``withhold-feedback="…"`` only has effect while editing the form fields. Whenever
the user clicks on the submit button of a form containing invalid data, then all fields which
did not validate, will show their error message together with an alert symbol and an alert border
(usually red).

Non-field errors need more validation logic and therefore are *always* detected by the server
implementation, usually by the ``clean()``-method of the form class.
