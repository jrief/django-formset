.. _dialog-forms:

============
Dialog Forms
============

Dialog forms are a way to create a form that is displayed in a dialog box. In **django-formset**
this is possible by using a :class:`formset.collection.FormCollection` and as one of its members,
an instance of type :class:`formset.dialog.DialogForm`. This is very similar to a setup as described
in :ref:`nested-collection`. The difference is that such a dialog form is not displayed by default,
and hence shall be used for additional, but optional fields. Otherwise, there is no difference in
the data structure, regardless of using a normal form or a dialog form as a member of a collection.

This example shows how to use an ``Activator`` field to open and close a dialog form:

.. django-view:: coffee_collection
	:caption: form.py

	from django.forms.fields import CharField, ChoiceField
	from django.forms.forms import Form
	from django.forms.widgets import RadioSelect
	from formset.collection import FormCollection
	from formset.dialog import ApplyButton, CancelButton, DialogForm
	from formset.fields import Activator
	from formset.renderers import ButtonVariant
	from formset.widgets import Button

	class CoffeeForm(Form):
	    flavors = Activator(
	        label="Add flavors",
	        help_text="Open the dialog to edit flavors",
	    )
	    nickname = CharField()

	class FlavorForm(DialogForm):
	    title = "Choose a Flavor"
	    induce_open = 'coffee.nickname == "Cappuccino" || coffee.flavors:active'
	    induce_close = '.cancel:active || .apply:active'

	    flavors = ChoiceField(
	        choices=(
	            ('caramel', "Caramel Macchiato"),
	            ('cinnamon', "Cinnamon Dolce Latte"),
	            ('hazelnut', "Turkish Hazelnut"),
	            ('vanilla', "Vanilla Latte"),
	            ('chocolate', "Chocolate Fudge"),
	            ('almonds', "Roasted Almonds"),
	            ('cream', "Irish Cream"),
	        ),
	        widget=RadioSelect,
	    )    
	    cancel = Activator(
	        label="Close",
	        widget=CancelButton,
	    )
	    apply = Activator(
	        label="Apply",
	        widget=ApplyButton,
	    )

	class CoffeeOrderCollection(FormCollection):
	    legend = "Order your coffee"
	    coffee = CoffeeForm()
	    flavor = FlavorForm()

This Form Dialog class has a few special attributes:


.. rubric:: ``title``
 
The title of the dialog form, shown in the header.


.. rubric:: ``induce_open``

A JavaScript expression that determines when the dialog form is opened. It opens when this
expression evaluates to ``true``. The expression is evaluated in the context of the collection form,
so you can refer to other fields accessing them through their path.

Here we check if the field "Nickname" contains the word "Cappuccino", and if so opens the dialog.
Another way of opening the dialog is to activate the button labeled "Add flavors".


.. rubric:: ``induce_close``

A JavaScript expression that determines when the dialog form is closed. It closes when this
expression evaluates to ``true``. Here we allow two fields to close the dialog: the "Cancel" button
and the "Apply" button. They provide different parameters to the underlying dialog functionality:
``CancelButton`` closes the dialog without applying any changes, while ``ApplyButton`` closes the
dialog and applies the changes to the form.


.. rubric:: ``prologue`` and ``epilogue``

These are optional attributes that can be used to add additional text to the dialog form. They are
rendered before and after the form fields, respectively. If this text contains HTML, remember to
mark the strings as safe using the Django ``mark_safe`` function.


.. rubric:: ``ApplyButton`` and ``CancelButton``

These special buttons shall only be used in classes inheriting from ``DialogForm``. They are
syntactic sugar for:

.. code-block:: python

	ApplyButton = Button(action='activate("apply")', button_variant=ButtonVariant.PRIMARY)

	CancelButton = Button(action='activate("cancel")', button_variant=ButtonVariant.SECONDARY)

The ``CoffeeOrderCollection`` then puts everything together and is rendered by a Django view:

.. django-view:: coffee_view
	:view-function: CoffeeOrderView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'coffee-result'}, collection_kwargs={'auto_id': 'cr_id_%s', 'renderer': FormRenderer(field_css_classes='mb-3')})
	:hide-code:

	from formset.renderers.bootstrap import FormRenderer
	from formset.views import FormCollectionView

	class CoffeeOrderView(FormCollectionView):
	    collection_class = CoffeeOrderCollection
	    template_name = "form-collection.html"
	    success_url = "/success"

The dialog form is rendered as a ``<dialog>`` element, which recently has been added to the HTML
standard. Its main child element is a ``<form method="dialog">`` which is submitted via the dialog
method. The states of the form controls are saved but not submitted, and the ``returnValue``
property gets set to the value of the button that was activated. This is why we have to pass
different arguments ("apply", "cancel")  to the closing buttons.

If a collection implements more than one Dialog Form, some or all of them can be opened
simultaneously. To prevent them from overlapping, these dialogs can be dragged to any position on
the screen, simply by clicking on their header and moving them around.


Modal Dialogs
=============

A special case of dialog forms are modal dialogs. They are displayed in a modal window, which
prevents the user from interacting with the rest of the page until the dialog is closed. This is
achieved by setting the attribute ``is_modal = True`` in the class inheriting from ``DialogForm``.

.. note:: Use modal dialogs with caution, as they can be annoying to users. They should only be used
	when it is absolutely necessary to interrupt the user's workflow.

Here is an example of a modal dialog form:

.. django-view:: terms_of_use_collection
	:caption: form.py

	from django.forms.fields import BooleanField, CharField
	from django.forms.forms import Form
	from django.utils.safestring import mark_safe
	from formset.collection import FormCollection
	from formset.dialog import ApplyButton, CancelButton, DialogForm
	from formset.fields import Activator
	from formset.renderers import ButtonVariant
	from formset.widgets import Button

	class AcceptDialogForm(DialogForm):
	    title = "Terms of Use"
	    epilogue = mark_safe("""
	        <p>This site does not allow content or activity that:</p>
	        <ul>
	            <li>is unlawful or promotes violence.</li>
	            <li>shows sexual exploitation or abuse.</li>
	            <li>harasses, defames or defrauds other users.</li>
	            <li>is discriminatory against other groups of users.</li>
	            <li>violates the privacy of other users.</li>
	        </ul>
	        <p><strong>Before proceeding, please accept the terms of use.</strong></p>
	    """)
	    induce_open = 'submit:active'
	    induce_close = '.close:active'
	    close = Activator(
	        label="Close",
	        widget=CancelButton,
	    )
	
	class UserNameForm(Form):
	    full_name = CharField(
	        label="Full Name",
	        max_length=100,
	    )
	    accept_terms = BooleanField(
	        label="Accept terms of use",
	        required=False,
	    )
	
	class AcceptTermsCollection(FormCollection):
	    legend = "Edit User Profile"
	    user = UserNameForm()
	    accept = AcceptDialogForm(is_modal=True)
	    submit = Activator(
	        label="Submit",
	        widget=Button(
	            action='user.accept_terms ? submit -> reload !~ scrollToError : activate',
	            button_variant=ButtonVariant.PRIMARY,
	            icon_path='formset/icons/send.svg',
	        ),
	    )

Here the ``AcceptDialogForm`` actually does not contain any form fields, but only some informative
text that is displayed to the user. The dialog is opened when the user clicks the "Submit" button,
but has forgotten to enable the checkbox labled "Accept terms of use". If the user clicks on the
"Submit" button, with that checkbox enabled, then the form is submitted and the page is reloaded.
This differing behaviour is achieved by using the ternary operator
``condition ? action-queue-1 : action-queue-1``. As condition we use the path to the field named
``user.accept_terms``. If this field evaluates to ``true``, the first action queue is executed,
otherwise the second one. The latter just activates the button named ``submit`` which then is
evaluated by the attribute ``induce_open = 'submit:active'`` in the dialog form named
``AcceptDialogForm``.


.. django-view:: terms_of_use_view
	:view-function: TermsOfUseView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'terms-result'}, collection_kwargs={'auto_id': 'tou_id_%s', 'renderer': FormRenderer(field_css_classes='mb-3')})
	:hide-code:

	from formset.renderers.bootstrap import FormRenderer
	from formset.views import FormCollectionView

	class TermsOfUseView(FormCollectionView):
	    collection_class = AcceptTermsCollection
	    template_name = "collection-no-button.html"
	    success_url = "/success"
