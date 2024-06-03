.. _model-collections:

========================================
Creating Collections from related Models
========================================

In more complex setups, we might want to change the contents of related models altogether. This is
when we start to use Form Collections to edit more than one `ModelForm`_. This is similar to what
Django's `Model formsets`_ functionality is intended for, but implemented in a more flexible way.


One-to-One Relations
====================

Let's start with a simple example. Say that we want to extend the `Django User model`_ with an extra
field, for instance a phone number field. Since we don't want to `substitute the User model`_
against a customized implementation, instead we must extend it using a `one-to-one relation`_.

.. code-block:: python
	:caption: models.py

	from django.conf import settings
	from django.db import models

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

In a typical application we might want to edit this model together with the default ``User`` model.
If we do this in the Django admin, we have to create an `InlineModelAdmin`_ with exactly one extra
form in the formset. This however implies that our model ``ExtendUser`` has a foreign relation
with the ``User`` model rather than a one-to-one relation [#f1]_ . In **django-formset** we can
handle this by declaring one ``ModelForm`` for ``User`` and ``ExtendUser`` each, and then group
those two forms into one ``FormCollection``.

.. django-view:: user_collection
	:hide-view:
	:caption: collections.py

	from django.forms.models import ModelForm, construct_instance, model_to_dict
	from formset.collection import FormCollection
	from testapp.models import ExtendUser, User

	class UserForm(ModelForm):
	    class Meta:
	        model = User
	        fields = '__all__'

	class ExtendUserForm(ModelForm):
	    class Meta:
	        model = ExtendUser
	        fields = ['phone_number']

	    def model_to_dict(self, user):
	        try:
	            return model_to_dict(user.extend_user, fields=self._meta.fields, exclude=self._meta.exclude)
	        except ExtendUser.DoesNotExist:
	            return {}
	
	    def construct_instance(self, user):
	        try:
	            extend_user = user.extend_user
	        except ExtendUser.DoesNotExist:
	            extend_user = ExtendUser(user=user)
	        form = ExtendUserForm(data=self.cleaned_data, instance=extend_user)
	        if form.is_valid():
	            construct_instance(form, extend_user)
	            form.save()

	class UserCollection(FormCollection):
	    user = UserForm()
	    extend_user = ExtendUserForm()

When this form collection is rendered and completed by the user, the submitted data from both forms
in this collection is, as expected, unrelated. We therefore have to tell one of the two forms, how
their generating models relate to each other. For this to work, each ``FormCollection`` and each
Django ``Form`` can implement two methods, ``model_to_dict(…)`` and ``construct_instance(…)``.

.. rubric:: ``model_to_dict(main_object)``

This method creates the initial data for a form starting from ``main_object`` as reference. It is
inspired by the Django global function ``model_to_dict(instance, fields=None, exclude=None)`` which
returns a Python dict containing the data in argument ``instance`` suitable for passing as a form's
``initial`` keyword argument.

The ``main_object`` is determined by the view (inheriting from
:class:`formset.views.EditCollectionView`) which handles our collection named ``UserCollection``,
using the ``get_object()``-method (usually by resolving a primary key or slug). 

.. rubric:: ``construct_instance(main_object)``

This method takes the ``cleaned_data`` from the validated form and applies it to one of the model
objects which are related with the ``main_object``. It is inspired by the Django global function 
``construct_instance(form, instance, fields=None, exclude=None)`` which constructs and returns a
model instance from the bound ``form``'s ``cleaned_data``, but does not save the returned instance
to the database.

Since form collections can be nested, method ``model_to_dict(…)`` can be used to recursively create
a dictionary to initialize the forms, starting from a main model object. After receiving the
submitted form data by the client, method ``construct_instance`` can be used to recursively traverse
the ``cleaned_data`` dictionary returned by the rendered form collection, in order to construct the
model objects somehow related to the ``main_object``.

To get this example to work, we therefore have to implement those two methods in our
``ExtendUserForm``. They both resolve the relation starting from the main object, in this
case the ``User`` object. Since we have a *one-to-one* relation, there can only be *no* or *one*
related ``ExtendUser`` object. If there is none, create it.

Finally, our ``UserCollection`` must be made editable and served by a Django view class. Since this
is a common use case, **django-formset** offers the class :class:`formset.views.EditCollectionView`
which is specialized in editing related models starting from a dedicated object. The latter usually
is determined by using a unique identifier, for instance its primary key or a slug.

.. django-view:: extend_user
	:view-function: type('UserCollectionView', (SessionFormCollectionViewMixin, model_collections.UserCollectionView), {}).as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'extend-user'}, collection_kwargs={'renderer': FormRenderer(field_css_classes='mb-3')})
	:caption: views.py

	from formset.views import EditCollectionView
	from testapp.models.user import User

	class UserCollectionView(EditCollectionView):
	    model = User
	    collection_class = UserCollection
	    template_name = 'form-collection.html'

This view then must be connected to the ``urlpatterns`` in the usual way. The template referenced by
this view shall contain HTML with a structure similar to this:

.. code-block:: django

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {{ form_collection }}
	  <button type="button" df-click="submit -> proceed !~ scrollToError">Submit</button>
	</django-formset>


One-to-Many Relations
=====================

One of the most prominent use-cases is to edit a model object together with child objects referring
to itself. By children we mean objects which point onto the main object using a Django
`ForeignKey`_. Let's again explain this using an example. Say, we want to create models for the
organization chart of a company. There is a model for a company, which may consist of different
departments, which themselves can have different teams. In relational models this usually is done
using a foreign key. For demonstration purposes the remaining part of the models is very lean and
only stores their names.

.. code-block:: python
	:caption: models.py

	from django.db import models
	
	class Company(models.Model):
	    name = models.CharField(verbose_name="Company name", max_length=50)
	
	class Department(models.Model):
	    name = models.CharField(verbose_name="Department name", max_length=50)
	    company = models.ForeignKey(Company, on_delete=models.CASCADE)
	
	    class Meta:
	        unique_together = ['name', 'company']
	
	class Team(models.Model):
	    name = models.CharField(verbose_name="Team name", max_length=50)
	    department = models.ForeignKey(Department, on_delete=models.CASCADE)
	
	    class Meta:
	        unique_together = ['name', 'department']

We immediately see that these models have a hierarchy of three levels. In classic Django, creating a
form to edit them altogether is not an easy task. To solve this, **django-formset** offers the
possibility to let form collections have siblings. We then can create forms and collection to edit
the company, its departments and their teams as:

.. django-view:: company_collection
	:hide-view:
	:caption: collections.py

	from django.forms.fields import IntegerField
	from django.forms.widgets import HiddenInput
	from django.forms.models import ModelForm
	from formset.collection import FormCollection
	from testapp.models import Company, Department, Team
	
	class TeamForm(ModelForm):
	    id = IntegerField(required=False, widget=HiddenInput)
	
	    class Meta:
	        model = Team
	        fields = ['id', 'name']
	
	class TeamCollection(FormCollection):
	    min_siblings = 0
	    team = TeamForm()
	    legend = "Teams"
	    add_label = "Add Team"
	    related_field = 'department'
	
	    def retrieve_instance(self, data):
	        if data := data.get('team'):
	            try:
	                return self.instance.teams.get(id=data.get('id') or 0)
	            except (AttributeError, Team.DoesNotExist, ValueError):
	                return Team(name=data.get('name'), department=self.instance)
	
	class DepartmentForm(ModelForm):
	    id = IntegerField(required=False, widget=HiddenInput)
	
	    class Meta:
	        model = Department
	        fields = ['id', 'name']
	
	class DepartmentCollection(FormCollection):
	    min_siblings = 0
	    department = DepartmentForm()
	    teams = TeamCollection()
	    legend = "Departments"
	    add_label = "Add Department"
	    related_field = 'company'
	
	    def retrieve_instance(self, data):
	        if data := data.get('department'):
	            try:
	                return self.instance.departments.get(id=data.get('id') or 0)
	            except (AttributeError, Department.DoesNotExist, ValueError):
	                return Department(name=data.get('name'), company=self.instance)
	
	class CompanyForm(ModelForm):
	    class Meta:
	        model = Company
	        fields = '__all__'
	
	class CompanyCollection(FormCollection):
	    company = CompanyForm()
	    departments = DepartmentCollection()

As we expect, we see that every Django model is represented by its form. Since we want to edit more
instances of the same model type, we somehow need a way to distinguish them. This is where the form
field named ``id`` comes into play. It is a hidden ``IntegerField`` and represents the primary key
of the model instances ``Department`` or ``Team``. Since newly created instances haven't any primary
key yet, it is marked with ``required=False`` to make it optional.

Finally, our ``CompanyCollection`` must be made editable and served by a Django view class. Here we
can use the the view class :class:`formset.views.EditCollectionView` as in the previous example.

.. django-view:: company_view
	:view-function: type('CompanyCollectionView', (SessionFormCollectionViewMixin, model_collections.CompanyCollectionView), {}).as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'company-collection'}, collection_kwargs={'renderer': FormRenderer(field_css_classes='mb-2')})
	:swap-code:
	:caption: views.py

	class CompanyCollectionView(EditCollectionView):
	    model = Company
	    collection_class = CompanyCollection
	    template_name = 'form-collection.html'

The view class ``CompanyCollectionView`` is specialized in editing related models starting from a
dedicated object. The latter usually is determined by using a unique identifier, for instance its
primary key or a slug.

.. rubric:: ``related_field``

In this example we have to implement the attribute ``related_field`` in our main collection class
``CompanyCollection``. This is because **django-formset** otherwise does not know how the
``DepartmentCollection`` is related to model ``Company``, and how the ``TeamCollection`` is related
to model ``Department``. 

.. rubric:: ``retrieve_instance(data)``

We recall that in the form declaration, we added a hidden field named ``id`` to keep track of the
primary key. During submission, we therefore must find the link between instances of type
``Department`` to their ``Company``, or between instances of type ``Team`` to their ``Department``.
Forms which have been added using the buttons "Add Team" or "Add Department" have an empty ``id``
field, because for obvious reasons, no primary key yet exists. For this to work we therefore have to
implement a custom method ``retrieve_instance(data)``. This method is responsible to retrieve the
wanted instance from the database, or if that hidden field is empty, must create an unsaved empty
model instance. Forms which have been deleted using the trash symbol on the upper right corner of
each form, are marked for removal and will be removed from the associated object.

.. rubric:: ``form_collection_valid(form_collection)``

After all submitted forms have been successfully validated, the ``EditCollectionView`` calls the
method ``form_collection_valid(form_collection)`` passing a nested structure of collections and
their associated forms. If the default implementation, doesn't match your needs, this method can be
overwritten by a customized implementation. If, as in this example, models are interconnected by a
straight relationship, the default implementation will probably suffice. Remember, that for more
complicated relationships, you can always overwrite methods ``construct_instance(…)`` and
``model_to_dict(…)`` to customize the conversion from the model instances to their forms and vice
versa.


.. [#f1] In technical terms, a one-to-one relation *is a* foreign key with an additional unique
	constraint.

.. _ModelForm: https://docs.djangoproject.com/en/stable/topics/forms/modelforms/
.. _Model formsets: https://docs.djangoproject.com/en/stable/topics/forms/modelforms/#model-formsets
.. _Django User model: https://docs.djangoproject.com/en/stable/ref/contrib/auth/#user-model
.. _substitute the User model: https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model
.. _one-to-one relation: https://docs.djangoproject.com/en/stable/ref/models/fields/#django.db.models.OneToOneField
.. _InlineModelAdmin: https://docs.djangoproject.com/en/stable/ref/contrib/admin/#inlinemodeladmin-objects
.. _ForeignKey: https://docs.djangoproject.com/en/stable/ref/models/fields/#foreignkey
