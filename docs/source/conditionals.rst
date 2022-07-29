.. _conditionals:

==========================================
Conditional Field and Fieldset Expressions
==========================================

Sometimes it doesn't make sense to render all fields of a form. Consider for instance a
questionnaire of a radiologist, who wants to know if the patient is pregnant. If that patient
is a male, he might even be offended by that question. The most user friendly solution to this is to
hide or disable such a field.

**django-formset** offers three conditionals:

* ``show-if="condition"``: The field or fieldset is only shown if the condition evaluates to true.
* ``hide-if="condition"``: The field or fieldset is only shown if the condition evaluates to false.
* ``disable-if="condition"``: The field or fieldset is disabled if the condition evaluates to true.

The ``condition`` can be any logical JavaScript expression. It can contain comparison operators such
as ``==``, ``<`` or ``!=`` and logical operators such as ``&&``, ``||`` and ``!``. This conditional
expression also has access to all the values inside the complete ``<django-formset>``. Values from
fields in the same form can be accessed using a relative path, starting with dot, for instance
``.fieldname``. Values from fields in other forms can be accessed by specifying the complete path to
that field, for instance ``formname.fieldname``. This also works for deeply nested forms.

.. note:: Fields using the conditionals ``show-if="…"`` or ``hide-if="…"`` shall use the attribute
	``required=False`` during initialization. This is because otherwise Django's form validation
	rejects that field as required, meanwhile it has been hidden by the client. In case only visible
	fields are required, add some validation code to the ``clean()`` method of that form.


Example Form
------------

This form uses a conditional where the value of one field influences if another field is visible.

.. code-block:: python

	from django.forms import fields, forms, widgets
	
	class QuestionnaireForm(forms.Form):
	    full_name = fields.CharField(
	        label="Full Name",
	    )
	
	    gender = fields.ChoiceField(
	        label="Gender",
	        choices=[('m', "Male"), ('f', "Female")],
	        widget=widgets.RadioSelect,
	    )
	
	    pregnant = fields.BooleanField(
	        label="Are you pregnant?",
	        required=False,
	        widget=widgets.CheckboxInput(attrs={'show-if': ".gender=='f'"})
	    )

Here we add the conditional ``show-if=".gender=='f'"`` to the checkbox asking for pregnancy. Only
if the field ``gender`` contains value ``f``, then that checkbox is visible. The path for accessing
that variable is relative here, if it starts with a dot, then the named field from the same form is
evaluated. 


Example Fieldset
----------------

Conditionals can also be used on a Fieldset element. For example by using

.. code-block:: python

	class CustomerForm(Fieldset):
	    legend = "Customer"
	    hide_if = 'register.no_customer'

we can use the value of another field, here ``register.no_customer`` to hide the whole fieldset if
that value evaluates to true.
