.. _dialog-model-forms:

==================
Dialog Model Forms
==================

.. versionadded:: 1.5

Together with :ref:`dialog-forms`, **django-formset** also offers dialog *model* forms. These forms
are, as one might expect, bound to a Django model. They are very useful for a common use case:

*A form with a select element to choose an object from a foreign key relationship.* 

We typically use the :ref:`selectize` to offer a selection method for choosing from a foreign
relation. However, if that foreign relation does not yet exist, the user may want to add it on
the fly without leaving the current form. This is a widespread pattern in many web applications, and
**django-formset** provides a way to handle this as well.

Assume we have a form for an issue tracker. This form has a field for the issue's reporter, which
is a foreign key to the user model. If that user does not exist, we would have to switch to a
different form, create the reporter object there, return back to the current form and then select
the newly created user from the dropdown list. This is not very user-friendly, and we would like to
be able to add a new user on the fly using a dialog form.

.. django-view:: 1_reporter_dialog
	:caption: dialog.py
	:hide-view:

	from django.forms.fields import IntegerField
	from django.forms.widgets import HiddenInput
	from formset.dialog import DialogModelForm
	from formset.fields import Activator
	from formset.widgets import Button
	from testapp.models import Reporter

	class ChangeReporterDialogForm(DialogModelForm):
	    title = "Add/Edit Reporter"
	    induce_open = 'issue.edit_reporter:active || issue.add_reporter:active'
	    induce_close = '.change:active || .cancel:active'
	
	    id = IntegerField(
	        widget=HiddenInput,
	        required=False,
	        help_text="Primary key of Reporter object. Leave empty to create a new object.",
	    )
	    cancel = Activator(
	        widget=Button(action='activate("clear")'),
	    )
	    change = Activator(
	        widget=Button(
	            action='submitPartial -> setFieldValue(issue.reporter, ^reporter_id) -> activate("clear")',
	        ),
	    )
	
	    class Meta:
	        model = Reporter
	        fields = ['id', 'full_name']
	
	    def is_valid(self):
	        if self.partial:
	            return super().is_valid()
	        self._errors = {}
	        return True

Here we create the dialog form ``ChangeReporterDialogForm``. It inherits from ``DialogModelForm``
and is a combination of the well known Django ModelForm_ and :ref:`dialog-forms` from the previous
chapter. In class ``Meta`` we specify the model and the form fields. Since we also want to edit
existing objects from our model ``Reporter``, we need a hidden identifier for reference. Here we use
the hidden field named ``id``, which points to the primary key of an editable ``Reporter`` object.

.. _ModelForm: https://docs.djangoproject.com/en/stable/topics/forms/modelforms/

With the attributes ``induce_open`` and ``induce_close`` we declare the conditions when the dialog
shall be opened or closed respectively. The buttons to close the dialog are part of the dialog form
itself. Here one wants to close the dialog, when either the button named ``change`` or ``cancel`` is
activated. In order to open this dialog, the user must activate either the buttons named
``edit_reporter`` or ``add_reporter``. They are declared as ``Activator`` fields in the form
``IssueForm`` (see below).

The action queue added to the button named ``change`` is specified as:

.. code-block:: javascript

	submitPartial -> setFieldValue(issue.reporter, ^reporter_id) -> activate("clear")

Let's go through it in detail:

.. rubric:: ``submitPartial``

This submits the complete collection of forms but tells the accepting Django endpoint, to only
validate the current form, ie. ``ChangeReporterDialogForm``. Check method ``form_collection_valid``
in view ``IssueCollectionView`` on how this validated form is further processed (see below). The
response of this view then is handled over to the next action in the queue:

.. rubric:: ``setFieldValue(issue.reporter, ^reporter_id)``

This takes the field ``reporter_id`` from the response and applies it to the field named
``issue.reporter``. Here we must use the caret symbol ``^`` so that **django-formset** can
distinguish a server side response from another field in this collection of forms.

.. rubric:: ``activate("clear")``

This action just activates the button, so that ``induce_close`` is triggered to close the dialog.
The parameter "clear" then implies to clear all the fields.

.. django-view:: 2_issue_form
	:caption: form.py
	:hide-view:

	from django.forms.fields import CharField
	from django.forms.models import ModelChoiceField, ModelForm
	from formset.fields import Activator
	from formset.widgets import Button, Selectize
	from testapp.models import IssueModel

	class IssueForm(ModelForm):
	    title = CharField()
	    reporter = ModelChoiceField(
	        queryset=Reporter.objects.all(),
	        widget=Selectize(
	            search_lookup='full_name__icontains',
	        ),
	    )
	    edit_reporter = Activator(
	        widget=Button(
	            action='activate(prefillPartial(issue.reporter))',
	            attrs={'df-disable': '!issue.reporter'},
	        ),
	    )
	    add_reporter = Activator(
	        widget=Button(action='activate')
	    )
	
	    class Meta:
	        model = IssueModel
	        fields = ['title', 'reporter']

This is the main form of the collection and is used to edit the issue related fields. It just offers
one field named ``title``; this is just for demonstration purposes, a real application would of
course offer many more fields.

In addition to its lonely ``title`` field, this form offers the two activators as mentioned in the
previous section. They are named ``edit_reporter`` and ``add_reporter``. When clicked, they induce
the opening of the dialog form as already explained. However, the button ``edit_reporter`` is when
clicked, configured to "prefill" the form's content using the value of the field ``issue.reporter``.
Prefilling is done by fetching the form's related data from the server and changing the field's
values accordingly. Here the fields named ``id`` and ``full_name`` are filled with data fetched from
the server.

This feature allows a user to first select a reporter, and then edit its content using the given
dialog form.

We also add the attribute ``df-disable=!issue.reporter`` to the button labled "Edit Reporter" in
order to disable it when no reporter is selected.

.. django-view:: 3_issue_collection
	:caption: collection.py
	:hide-view:

	from django.forms.models import construct_instance
	from formset.collection import FormCollection

	class EditIssueCollection(FormCollection):
	    change_reporter = ChangeReporterDialogForm()
	    issue = IssueForm()
	
	    def construct_instance(self, main_object):
	        assert not self.partial
	        instance = construct_instance(self.valid_holders['issue'], main_object)
	        instance.save()
	        return instance

This form collection combines our issue editing form with the dialog form to edit or add a reporter.
Note that in this collection, method ``construct_instance`` has been overwritten. On submission, it
just constructs an instance of type ``IssueModel`` but ignores any data related to the ``Reporter``-
model. The latter is handled in method ``form_collection_valid`` as explained in the next section:

.. django-view:: 4_issue_view
	:view-function: type('IssueCollectionView', (SessionModelFormViewMixin, dialog_model_forms.IssueCollectionView), {}).as_view(template_name='form-collection.html', extra_context={'framework': 'bootstrap', 'pre_id': 'issue-result'}, collection_kwargs={'renderer': FormRenderer(field_css_classes='mb-2')})
	:swap-code:
	:caption: views.py

	from django.http import JsonResponse, HttpResponseBadRequest
	from formset.views import EditCollectionView

	class IssueCollectionView(EditCollectionView):
	    model = IssueModel
	    collection_class = EditIssueCollection
	
	    def form_collection_valid(self, form_collection):
	        if form_collection.partial:
	            if not (valid_holder := form_collection.valid_holders.get('change_reporter')):
	                return HttpResponseBadRequest("Form data is missing.")
	            if id := valid_holder.cleaned_data['id']:
	                reporter = Reporter.objects.get(id=id)
	                construct_instance(valid_holder, reporter)
	            else:
	                reporter = construct_instance(valid_holder, Reporter())
	            reporter.save()
	            return JsonResponse({'reporter_id': reporter.id})
	        return super().form_collection_valid(form_collection)

This view handles our form collection consisting of the two forms ``ChangeReporterDialogForm`` and
``IssueForm``. On a complete submission of this view, method ``form_collection_valid`` behaves
as implemented by default. However, since the dialog form is submitted partially, we use that
information to modify the default behavior:

If the hidden field named ``id`` has a value, the dialog form is opened to *edit* a reporter.
Therefore we fetch that object from the database and change it using the modified form's content.

If the hidden field named ``id`` has no value, the dialog form is opened to *add* a reporter.
Here we can just construct a new instance using an empty ``Reporter`` object.

In both cases, the primary key of the edited or added ``Reporter`` object is sent back to the
client using the statement ``JsonResponse({'reporter_id': reporter.id})``. Remember the button's
action ``setFieldValue(issue.reporter, ^reporter_id)`` as mentioned in the first section. This takes
that response value from ``reporter_id`` and applies it to the field named ``issue.reporter``. The
latter is implemented using the :ref:`selectize`, which in consequence fetches the server to receive
the new value for the edited or added ``Reporter`` object.
