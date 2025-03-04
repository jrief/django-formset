.. _conditionals:

==========================================
Conditional Field and Fieldset Expressions
==========================================

Sometimes it doesn't make sense to render all fields of a form. Consider for instance a
questionnaire of a radiologist, who needs to know if his patient is pregnant. Some male patients
might be offended by that question. The most user-friendly solution to this is to hide or disable
such a field.

For this purpose **django-formset** offers three conditionals:

* ``df-show="<condition>"``: The field or fieldset is only shown if the ``<condition>`` evaluates to
  true.
* ``df-hide="<condition>"``: The field or fieldset is only shown if the ``<condition>`` evaluates to
  false.
* ``df-disable="<condition>"``: The field or fieldset is disabled if the ``<condition>`` evaluates
  to true.

The ``<condition>`` can be any logical JavaScript expression. It can contain comparison operators
such as ``==``, ``<`` or ``!=`` and logical operators such as ``&&``, ``||`` and ``!``. This
conditional expression also has access to all the values in the complete context of its own
``<django-formset>``. Values from fields in the same form can be accessed using a relative path,
starting with dot, for instance ``.fieldname``. Values from fields in other forms can be accessed by
specifying the complete path to that field, for instance ``formname.fieldname``. This also works for
deeply nested forms.

.. note:: Fields using the conditionals ``df-show="…"`` or ``df-hide="…"`` shall use the attribute
	``required=False`` during initialization. This is because otherwise Django's form validation
	rejects that field as required, meanwhile it has been hidden by the client. In case only visible
	fields are required, adopt the validation code of the ``clean()``-method in the corresponding
	form class.


Questionnaire Form
==================

This form uses a conditional where the value of one field influences if another field is visible.

.. django-view:: questionaire_form
	:hide-view:
	:emphasize-lines: 15

	from django.forms import fields, forms, widgets
	
	class QuestionnaireForm(forms.Form):
	    full_name = fields.CharField(label="Full Name")

	    gender = fields.ChoiceField(
	        label="Gender",
	        choices=[('f', "Female"), ('m', "Male")],
	        widget=widgets.RadioSelect,
	    )
	
	    pregnant = fields.BooleanField(
	        label="Are you pregnant?",
	        required=False,
	        widget=widgets.CheckboxInput(attrs={'df-show': ".gender=='f'"})
	    )

Here we add the conditional ``df-show=".gender=='f'"`` to the checkbox asking for pregnancy. Only
if the field ``gender`` contains value ``f``, then that checkbox is visible. The path for accessing
that variable is relative here: If it starts with a dot, then the named field from the same form is
evaluated. 

.. django-view:: questionaire_view
	:view-function: QuestionnaireView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'questionaire-result'}, form_kwargs={'auto_id': 'qf_id_%s'})
	:hide-code:

	from formset.views import FormView 

	class QuestionnaireView(FormView):
	    form_class = QuestionnaireForm
	    template_name = "form.html"
	    success_url = "/success"


Conditional Fieldset
====================

Conditionals can also be used on a Fieldset element. For example by using

.. django-view:: conditional_fieldset
	:hide-view:

	from django.forms import fields, forms
	from formset.collection import FormCollection
	from formset.fieldset import Fieldset

	class CustomerForm(Fieldset):
	    legend = "Customer"
	    hide_condition = 'register.no_customer'

	    recipient = fields.CharField(label="Recipient")
	    email = fields.EmailField(label="Email", required=False)

	class RegisterForm(forms.Form):
	    no_customer = fields.BooleanField(
	        label="I'm not a customer",
	        required=False,
	    )

	class CustomerCollection(FormCollection):
	    customer = CustomerForm()
	    register = RegisterForm()

Here we use the value of the field ``no_customer`` in form ``RegisterForm``. If it evaluates to
true, the whole fieldset is hidden.

.. django-view:: conditional_collection
	:view-function: CustomerView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'collection-result'}, collection_kwargs={'renderer': FormRenderer(field_css_classes='mb-3')})
	:hide-code:

	from formset.views import FormCollectionView

	class CustomerView(FormCollectionView):
	    collection_class = CustomerCollection
	    template_name = "form-collection.html"
	    success_url = "/success"


Conditional Disable
===================

Conditionals can also be used to disable other fields. By using the attribute
``df-disable=<condition>`` we can disable a field, preventing the user to input data.

.. django-view:: accept_form
	:hide-view:

	class AcceptForm(forms.Form):
	    accept_terms = fields.BooleanField(
	        label="Accept terms and conditions",
	        required=False,
	    )

	    email = fields.EmailField(
	        label="Email",
	        widget=widgets.EmailInput(attrs={'df-disable': ".accept_terms==''"})
	    )

Here we use the value of the field ``accept_terms`` in form ``AcceptForm``. If it is unchecked the
email field is disabled.

.. django-view:: accept_view
	:view-function: AcceptView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'accept-result'}, form_kwargs={'auto_id': 'af_id_%s'})
	:hide-code:

	class AcceptView(FormView):
	    form_class = AcceptForm
	    template_name = "form.html"
	    success_url = "/success"

Please do not mix up the possibility of disabling a field with the functionality to
:ref:`auto-disable_buttons`, which is part of the form validation process.
