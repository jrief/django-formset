.. _model-collections:

========================================
Creating Collections from related Models
========================================

In more complex setups, we often want to change the contents of related models altogether. This is
when we start to use Form Collections to edit more than one `ModelForm`_. This is similar to what
Django's `Model formsets`_ functionality is intended for, but implemented in a more flexible way.


One-to-One Relations
====================

Let's start with a simple example. Say that we want to extend the `Django User model`_ with extra
fields, for instance a phone number field. Since we don't want to `substitute the User model`_
against our own implementation, instead we must extend it using a `one-to-one relation`_.

.. code-block:: python

	from django.conf import settings

	class ExtendUser(models.Model):
	    user = models.OneToOneField(
	        settings.AUTH_USER_MODEL,
	        on_delete=models.CASCADE,
	        related_name='extend_user',
	    )

	    phone_number = models.CharField(
	        verbose_name="Phone Number",
	        max_length=25,
	        blank=True,
	        null=True,
	    )

In a typical application we would like to edit this model together with the default ``User`` model.
If we do this in the Django admin, we have to create an `InlineModelAdmin`_ with exactly one extra
form in the formset. This however implies that our model ``ExtendUser`` has a foreign relation
with the ``User`` model rather than a one-to-one relation[#1]_. In **django-formset** we handle this 
by declaring one ``ModelForm`` for ``User`` and ``ExtendUser`` each, and then group those two forms
into one ``FormCollection``.

.. code-block:: python

	from django.contrib.auth import get_user_model
	from django.forms.models import ModelForm
	from formset.collection import FormCollection

	class UserForm(ModelForm):
	    class Meta:
	        model = get_user_model()
	        fields = '__all__'

	class ExtendUserForm(ModelForm):
	    class Meta:
	        model = ExtendUser
	        fields = ['phone_number']

	class UserCollection(FormCollection):
	    user = UserForm()
	    extend_user = ExtendUserForm()

When this form collection is rendered and completed by the user, the submitted data from both forms
in this collection is, as expected, unrelated. We therefore have to tell one of the two forms, how
their generating models relate to each other. For this to work, each ``FormCollection`` and each
Django ``Form`` can implement two methods, ``model_to_dict`` and ``construct_instance``.


.. rubric:: ``model_to_dict(main_object, fields=None, exclude=None)``

This method creates the initial data for a form starting from ``main_object`` as reference. It is
inspired by Django's global function ``model_to_dict(instance, fields=None, exclude=None)`` which
returns a dict containing the data in ``instance`` suitable for passing as a Form's ``initial``
keyword argument.

The ``main_object`` is determined by the view (inheriting from
:class:`formset.views.EditCollectionView`) which handles our form collection ``UserCollection``,
using the ``get_object``-method (usually by resolving a primary key or slug). 


.. rubric:: ``construct_instance(main_object, data)``

This method takes the ``cleaned_data`` from a validated form and applies it to one of the model
objects which are related with the ``main_object``. It is inspired by Django's global function 
``construct_instance(form, instance, fields=None, exclude=None)`` which construct and returns a
model instance from the bound ``form``'s ``cleaned_data``, but does not save the returned instance
to the database.

Since form collections can be nested, method ``model_to_dict`` can be used to recursively create a
dictionary to initialize the forms, starting from a main model object. After receiving the submitted
form data by the client, method ``construct_instance`` can be used to recursively traverse the
``cleaned_data`` dictionary returned by the rendered form collection, in order to construct the
model objects somehow related to the ``main_object``.

To get the example from above to work, we therefore have to implement those two methods in our
``ExtendUserForm``:

.. code-block:: python

	from django.forms.models import construct_instance, model_to_dict

	class ExtendUserForm(ModelForm):
	    ...

	    def model_to_dict(self, user):
	        try:
	            return model_to_dict(user.extend_user, fields=['phone_number'])
	        except ExtendUser.DoesNotExist:
	            return {}
	
	    def construct_instance(self, main_object, data):
	        try:
	            extend_user = main_object.extend_user
	        except ExtendUser.DoesNotExist:
	            extend_user = ExtendUser(user=main_object)
	        form = ExtendUserForm(data=data, instance=extend_user)
	        if form.is_valid():
	            construct_instance(form, extend_user)
	            form.save()

What both of these methods do, is to resolve the relation starting from the main object, in this
case the ``User`` object. Since we have a one-to-one relation, there can only be *no* or *one*
related ``ExtendUser`` object. If there is none, create it.

The view class serving as endpoint for ``UserCollection`` then can be written as

.. code-block:: python

	from django.contrib.auth import get_user_model
	from formset.views import EditCollectionView

	class UserCollectionView(EditCollectionView):
	    model = get_user_model()
	    collection_class = UserCollection
	    template_name = 'form-collection.html'

and added to the ``urlpatterns`` to usual way. The template referenced by that view shall contain
HTML with something like this:

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {{ form_collection }}
	  <button type="button" click="submit -> proceed !~ scrollToError">Submit</button>
	</django-formset>


One-to-Many Relations
=====================

One of the most prominent use-cases is to edit a model object together with child objects referring
to itself. By children we mean objects which point onto the main object using a Django
`ForeignKey`_. Let's again explain this using an example. Say, we want to extend the previous
example and allow more than one phone number per user. For this we replace the ``OneToOneField`` for
field ``user`` against a ``ForeignKey``. In practice, this means that we now have a flexible list of
phone numbers instead of just one. To solve this, **django-formset** offers the possibility to let
form collections have siblings. We then can rewrite our collection as:

.. code-block:: python

	class ExtendUserForm(ModelForm):
	    id = IntegerField(required=False, widget=HiddenInput)

	    class Meta:
	        model = ExtendUser
	        fields = ['phone_number']

	class ExtendCollection(FormCollection):
	    min_siblings = 0
	    extend = ExtendUserForm()

	    def model_to_dict(self, user):
	        opts = self.declared_holders['contact']._meta
	        return [{'contact': model_to_dict(contact, fields=opts.fields)}
	                for contact in user.contacts.all()]
	
	    def construct_instance(self, user, data):
	        for data in data:
	            try:
	                contact_object = user.contacts.get(id=data['contact']['id'])
	            except (KeyError, UserContact.DoesNotExist):
	                contact_object = UserContact(user=user)
	            form_class = self.declared_holders['contact'].__class__
	            form = form_class(data=data['contact'], instance=contact_object)
	            if form.is_valid():
	                if form.marked_for_removal:
	                    contact_object.delete()
	                else:
	                    construct_instance(form, contact_object)
	                    form.save()

	class UserCollection(FormCollection):
	    user = UserForm()
	    extend_list = ExtendCollection()

Here we also have to implement the two methods ``model_to_dict`` and ``construct_instance``
ourselves. Since the collection class ``ExtendCollection`` is declared to allow siblings, its
children forms are rendered as many times as objects of type ``ExtendUser`` point onto the main
object, in short the ``User`` object.

Here method ``model_to_dict`` instantiates a list. This list is a serialized representation of all
objects of type ``ExtendUser`` referring to the ``User`` (main) object.

After a submitted form has been validated, we start constructing as many models of type
``ExtendUser``, as the collections provides. Since we must link each form to its associated
object, each sub-form contains the primary key of that object as hidden field. Forms which have
been deleted by the user are marked for removal and will be removed from the main object.


.. _[#1]: In technical terms, a one-to-one relation *is a* foreign key with an additional unique
	constraint.

.. _ModelForm: https://docs.djangoproject.com/en/stable/topics/forms/modelforms/
.. _Model formsets: https://docs.djangoproject.com/en/stable/topics/forms/modelforms/#model-formsets
.. _Django User model: https://docs.djangoproject.com/en/stable/ref/contrib/auth/#user-model
.. _substitute the User model: https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model
.. _one-to-one relation: https://docs.djangoproject.com/en/stable/ref/models/fields/#django.db.models.OneToOneField
.. _InlineModelAdmin: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#inlinemodeladmin-objects
.. _ForeignKey: https://docs.djangoproject.com/en/stable/ref/models/fields/#foreignkey
