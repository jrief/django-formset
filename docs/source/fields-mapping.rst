.. _fields-mapping:

==============
Fields Mapping
==============

.. version-added:: 2.0

A class inheriting from a Django model may contain fields which accept arbitrary data stored as
JSON. Django itself, for that purpose provides a JSONField_ to store any kind of serializable data.

.. _JSONField: https://docs.djangoproject.com/en/stable/ref/models/fields/#jsonfield

When creating a form from a model, the input field associated with a ``JSONField``, typically is a
``<textarea ...></textarea>``. This textarea widget is very impracticable for editing, because it
just contains a textual representation of that object notation. One possibility is to use a generic
JSON editor, which with some JavaScript, transforms the widget into an attribute-value-pair editor.
This approach however requires us to manage the field keys ourselves. It furthermore prevents us
from utilizing all the nice features provided by the Django forms framework, such as field
validation, normalization of data and the usage of foreign keys.

By using **django-formset**, one can inherit from a Django ModelForm_, and store all, or a subset of
that form fields in one or more JSON fields inside of the associated model.

.. _ModelForm: https://docs.djangoproject.com/en/stable/topics/forms/modelforms/


Example
=======

Say, we have a Django model to describe a bunch of different products. The title and the price
fields are common to all products, whereas the properties can vary depending on its product type.
Since we don't want to create a different product model for each product type, we use a JSON field
to store these arbitrary properties.

.. code-block:: python
	:caption: models.py

	from django.db import models
	
	class ProductModel(models.Model):
	    title = models.CharField(max_length=50)
	    price = models.DecimalField(max_digits=5, decimal_places=2)
	    properties = models.JSONField(default=dict)

In a typical form editing view, we would create a form inheriting from ``ModelForm`` and refer to
this model using the ``model`` attribute in its ``Meta``-class. Then the field named ``properties``
would show up as unstructured JSON, rendered inside a ``<textarea ...></textarea>``. This definitely
is not what we want! Instead, we can map the fields of our form to the keys of the said JSON field.

.. django-view:: product_form
	:caption: forms.py
	:emphasize-lines: 18

	from django.forms import fields, widgets
	from formset.forms import ModelForm
	from testapp.models.product import ProductModel

	class ProductForm(ModelForm):
	    color = fields.RegexField(
	        regex=r'^#[0-9a-f]{6}$',
	        widget=widgets.TextInput(attrs={'type': 'color'}),
	    )
	    size = fields.ChoiceField(
	        choices=[('s', "small"), ('m', "medium"), ('l', "large"), ('xl', "extra large")],
	        widget=widgets.RadioSelect,
	    )
	
	    class Meta:
	        model = ProductModel
	        fields = ['title', 'price', 'color', 'size', 'properties']
	        fields_map = {'properties': ['color', 'size']}

Additionally, we add a special dictionary named ``fields_map`` to the ``Meta``-class of that form.
Inside this dictionary, the key (here ``properties``) refers to the JSON-field in our Django model
named ``ProductModel``. The value (here ``['color', 'size']``) is a list of named form fields,
declared in our form- or base-class of thereof. This allows us to assign all standard Django form
fields to arbitrary JSON fields declared in our Django model.

.. django-view:: product_view
	:view-function: ProductView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'product-result'}, form_kwargs={'auto_id': 'pr_id_%s'})
	:hide-code:

	from django.views.generic import UpdateView
	from formset.views import FormViewMixin
	from testapp.demo_helpers import SessionModelFormViewMixin

	class ProductView(SessionModelFormViewMixin, FormViewMixin, UpdateView):
	    model = ProductModel
	    form_class = ProductForm
	    template_name = "form.html"
	    success_url = "/success"

.. note:: After submission, the content of these form fields is stored in the database. Therefore
	after reloading this page, the same content will reappear in the form.

Due to the nature of JSON, indexing and thus building filters or sorting rules based on the fields
content is not as simple, as with standard model fields. Therefore this approach is best suited, if
the main focus is to store data, rather than digging through data.


Mapping Foreign Keys
====================

It even is possible to map foreign keys to a JSON field. This is useful when we want to store a
reference to another model object inside of a JSON field. In this case, we can use a
ModelChoiceField_ or a ModelMultipleChoiceField_ to refer to another model object using a generic
relation.

.. _ModelChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#modelchoicefield
.. _ModelMultipleChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#modelmultiplechoicefield

Foreign keys are stored as ``"fieldname": {"model": "appname.modelname", "pk": 1234}`` in our JSON
field, meaning that we have **no database constraints**. If a target object is deleted, that foreign
key points to nowhere. Therefore always keep in mind, that we don't have any
`referential integrity`_ and hence must write our code in a defensive manner.

Multiple foreign keys are stored as ``"fieldname": {"model": "appname.modelname", "p_keys": [12, 34, 56, ...]}``
in our JSON field, again without any **database constraints**.

**django-formset** provides this utility function to retrieve the instance of a single foreign key
stored inside a JSON field:

.. code-block:: python

	from formset.fieldsmapping import get_related_object

	related_object = get_related_object(
	    json_field_value,  # the value of the JSON field
	    'fieldname',       # the name of the field in the JSON object
	)


**django-formset** provides this utility function to retrieve a queryset of instances for a list of
foreign keys stored inside a JSON field:

.. code-block:: python

	from formset.fieldsmapping import get_related_queryset

	related_queryset = get_related_queryset(
	    json_field_value,  # the value of the JSON field
	    'fieldname',       # the name of the field in the JSON object
	)

Both functiond return ``None`` if the given field name is not present in the JSON object, or if it
doesn't exist on the model, or if the foreign key points to a non-existing object.

.. _referential integrity: https://en.wikipedia.org/wiki/Referential_integrity


Implementation Details
======================

My other library `django-entangled`_ provides a similar solution for this problem. It can however
not be combined seamlessly with **django-formset**, because both libraries are based on the same
concept of overriding the form's ``Meta`` class. This is why I decided to integrate its
functionality into **django-formset** using a slightly different approach.

.. _django-entangled: https://github.com/jrief/django-entangled
