.. _collection-fields:

=================
Collection Fields
=================

.. version-added:: 2.0

Until version 2.0, collections could only hold forms or other collections. When using collections to
store their values into multiple Django models, usually by using related foreign keys, the developer
must add a hidden field to represent the primary key of the model instances.

In **django-formset** version 2.0, developers can create deeply nested form collections and store
their values as structured data in a single JSONField_.

.. _JSONField: https://docs.djangoproject.com/en/stable/ref/models/fields/#jsonfield

The advantage of keeping form data as JSON is, that developers don't have to unroll collections,
when converting the data from their models into forms and vice versa. The downside of this
approach is that the data remains unstructured, making it difficult to find information.

For this purpose, **django-formset** provides the special form field
:class:`formset.formfields.collection.CollectionField`. It takes all the `core arguments`_ of the
Django form ``Field`` class, plus an instance of any :ref:`form-collections`. When rendered, this
``CollectionField`` then is replaced by the forms and fields of that collection. A
``CollectionField`` therefore does not render a label unless explicitly set, because each sub-field
provides their own labels anyway.

.. _core arguments: https://docs.djangoproject.com/en/stable/ref/forms/fields/#core-field-arguments

On the model side, the content of a :class:`formset.formfields.CollectionField` typically is stored
in a JSONField_.


Examples
========

The ``CollectionField`` can be used in two different ways. It can either be used as a form field to
map its content as shown in section :ref:`fields-mapping`. Or it can be used to store the content
directly in a JSONField_ provided by the used model.


Using ``fields_map``
--------------------

Say, we want to store the configuration for an HTML component to represent a carousel_ using Django
models. For this we would require at least two models: one to represent the carousel itself and
one to represent the slides of the carousel. But since carousel slides typically are not that
interesting by themselves, we can forgo a foreign relationship and instead store everything inside a
``JSONField``. This representation then contains a dictionary with the configuration of the carousel
and a list of dictionaries containing the configuration for each of the slides.

.. _carousel: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_overflow/CSS_carousels

.. code-block:: python
   :caption: models.py

	from django.db import models
	
	class Component(models.Model):
	    type = models.CharField(max_length=16)
	    context = models.JSONField(default=dict)

This model by the way has the advantage of being reusable for other kinds of HTML components.

Now, instead of creating a model for the carousel and one for each slide, we create a collection of
forms to represent that structure. Each slide and the carousel are represented by their forms, and
the collection is used to glue them together.

.. django-view:: carousel_form
	:caption: forms.py

	from django.forms import fields, forms
	from formset.collection import AddSiblingActivator, FormCollection
	from formset.formfields.collection import CollectionField
	from formset.formfields.richtext import RichTextField
	from formset.forms import ModelForm
	from formset.widgets import UploadedFileInput
	
	from testapp.models import Component
	
	class SlideForm(forms.Form):
	    title = fields.CharField(
	        label="Slide Title",
	        max_length=100,
	    )
	    image = fields.ImageField(
	        label="Image",
	        widget=UploadedFileInput,
	    )
	    caption = RichTextField(
	        label="Slide Description",
	        required=False,
	    )
	
	class SlideCollection(FormCollection):
	    legend = "Carousel Slides"
	    min_siblings = 1
	    max_siblings = 10
	    is_sortable = True
	    slide_form = SlideForm()
	    induce_add_sibling = '.add_slide:active'
	    ignore_marked_for_removal = True
	    add_slide = AddSiblingActivator("Add Slide")

	class CarouselForm(ModelForm):
	    auto_start = fields.BooleanField(
	        label="Auto Start",
	        required=False,
	    )
	    interval = fields.IntegerField(
	        label="Interval in milliseconds",
	        min_value=1,
	        required=False,
	        help_text="Slides do not auto start, if this value is not set.",
	    )
	    slides = CollectionField(SlideCollection)

	    class Meta:
	        model = Component
	        fields = ['context']
	        fields_map = {'context': ['auto_start', 'interval', 'slides']}


.. django-view:: carousel_view
	:view-function: CarouselEditView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'carousel-result'}, form_kwargs={'auto_id': 'cs_id_%s', 'renderer': FormRenderer(field_css_classes='mb-2')}, filtered_type='carousel')
	:hide-code:

	from django.views.generic import UpdateView
	from formset.renderers.bootstrap import FormRenderer
	from formset.upload import FileUploadMixin
	from formset.views import FormViewMixin
	from testapp.demo_helpers import SessionModelFormViewMixin
	
	class ComponentFormViewMixin:
	    filtered_type = None
	
	    def get_queryset(self):
	        queryset = super().get_queryset()
	        return queryset.filter(type=self.filtered_type)
	
	    def form_valid(self, form):
	        form.instance.type = self.filtered_type
	        return super().form_valid(form)
	
	class CarouselEditView(ComponentFormViewMixin, FileUploadMixin, SessionModelFormViewMixin, FormViewMixin, UpdateView):
	    model = Component
	    form_class = CarouselForm
	    template_name = "form.html"
	    success_url = "/success"

On submission, the serialized representation of all of the fields in the ``Meta``-class
``fields_map`` then is stored in the ``context`` field of the ``Component`` model. Since
``SlideCollection`` is configured to have siblings, this is stored as a list of dictionaries.
Otherwise, if the collection would not have siblings, this would just be a sub-dictionary.

.. note:: After submission, the carousel configuration is stored in the database. Therefore, after
	reloading this page, the same images and captions will reappear.


Store content from a ``CollectionField`` into a ``JSONField``
-------------------------------------------------------------

In this example, we want to represent an accordion_ element as our HTML component. There we do not
need to keep any configuration for the accordion itself, only the configuration of its items must be
stored. We therefore can map the field named ``context`` directly onto the equally named
``JSONField`` in our model ``Component``.

.. _accordion: https://en.wikipedia.org/wiki/Accordion_(GUI)

.. django-view:: accordion_form
	:caption: forms.py

	from django.forms import fields, forms
	from formset.collection import FormCollection
	from formset.formfields.collection import CollectionField
	from formset.formfields.richtext import RichTextField
	from formset.forms import ModelForm
	
	from testapp.models.component import Component
	
	class AccordionItem(forms.Form):
	    heading = fields.CharField(
	        label="Accordion Heading",
	        max_length=100,
	    )
	    body = RichTextField(
	        label="Accordion Body",
	        required=False,
	    )
	
	class AccordionCollection(FormCollection):
	    min_siblings = 0
	    extra_siblings = 0
	    accordion_item = AccordionItem()
	    legend = "Accordion"
	    induce_add_sibling = '.add_accordion_item:active'
	    ignore_marked_for_removal = True
	    add_accordion_item = AddSiblingActivator("Add Accordion Item")

	class AccordionForm(ModelForm):
	    context = CollectionField(AccordionCollection)
	
	    class Meta:
	        model = Component
	        fields = ['context']

.. django-view:: accordion_view
	:view-function: AccordionEditView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'accordion-result'}, form_kwargs={'auto_id': 'acc_id_%s', 'renderer': FormRenderer(field_css_classes='mb-2')}, filtered_type='accordion')
	:hide-code:
	
	class AccordionEditView(ComponentFormViewMixin, FileUploadMixin, SessionModelFormViewMixin, FormViewMixin, UpdateView):
	    model = Component
	    form_class = AccordionForm
	    template_name = "form.html"
	    success_url = "/success"

On submission, the serialized representation of all accordion items is now stored directly in the
``context`` field of the ``Component`` model, but this time without any field mapping. Since
``AccordionCollection`` is configured to have siblings, this is stored as a list of dictionaries.
Otherwise, if the collection would not have siblings, this would just be a dictionary. When using a
collection with siblings, assure to use it with a JSONDecoder_ with ``strict=False``, which is the
default anyway. This is because the stored JSON then is a list rather then a dictionary.

.. _JSONDecoder: https://docs.python.org/3/library/json.html#json.JSONDecoder

.. note:: After submission, the accordion item configuration is stored in the database. Therefore,
	after reloading this page, the same images and captions will reappear.
