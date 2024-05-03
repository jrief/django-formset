.. _model_forms:

==========================
Creating Forms from Models
==========================

Just as in Django, forms can be created from models and rendered by **django-formset**.  

Say, we use a model similar to that described in the Django documentation, ie.
``myapp.models.Article``:

.. code-block:: python
	:caption: models.py

	from django.db import models

	class Reporter(models.Model):
	    full_name = models.CharField(max_length=70)

	class Article(models.Model):
	    pub_date = models.DateField()
	    headline = models.CharField(max_length=200)
	    content = models.TextField()
	    reporter = models.ForeignKey(Reporter, on_delete=models.CASCADE)
	    teaser = models.FileField(
	        upload_to='images',
	        blank=True,
	        help_text="Maximum file size for uploading is 1MB",
	    )

We then use that model to create a form class. There however is a caveat: Some Django widgets used
for rendering HTML fields shall or must be replaced by alternative widgets offered by the 
**django-formset**-library. This is because, compared to their pure HTML counterpart, they greatly
enhance the user experience functionality of many input elements. When using a ``FileField``, the
widget *must* be replaced, because an asynchronous file upload otherwise wouldn't work.

More on this topic can be found in :ref:`alternative-widgets`.

The form to edit the above model ``Article`` shall optionally override field ``reporter`` which
contains more than 900 entries and therefore is user unfriendly to be rendered by a HTML
``<select>``-element. It also must override field ``teaser`` which is used to accept uploaded files.
The widget for field ``pub_date`` shall be replaced by a ``DateInput``, because that enforces a
client-side validation of inputted dates. The field ``content`` is overridden by the widget
``RichtextArea``, allowing to format the text using various styles.

.. django-view:: article_form
	:caption: forms.py

	from django.forms.models import ModelForm
	from formset.richtext.widgets import RichTextarea
	from formset.widgets import DateInput, Selectize, UploadedFileInput
	from testapp.models.article import Article

	class ArticleForm(ModelForm):
	    class Meta:
	        model = Article
	        fields = ['pub_date', 'headline', 'content', 'reporter', 'teaser']
	        widgets = {
	            'pub_date': DateInput,
	            'content': RichTextarea,
	            'reporter': Selectize(search_lookup='full_name__icontains'),
	            'teaser': UploadedFileInput,
	        }


Detail View for ``ModelForm``
=============================

To display and validate data from this ``Article``, we use the well known detail view offered by
Django for `updating models`_:

.. _updating models: https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#django.views.generic.edit.UpdateView

.. django-view:: article_view
	:view-function: type('ArticleEditView', (SessionModelFormViewMixin, model_forms.ArticleEditView), {}).as_view(extra_context={'framework': 'bootstrap'})
	:caption: views.py

	from django.views.generic import UpdateView
	from formset.upload import FileUploadMixin
	from formset.views import FormViewMixin, IncompleteSelectResponseMixin

	class ArticleEditView(FileUploadMixin, IncompleteSelectResponseMixin, FormViewMixin, UpdateView):
	    model = Article
	    form_class = ArticleForm
	    template_name = 'form.html'
	    success_url = '/success'

.. note:: After submission, the content of these form fields is stored in the database. Therefore
	after reloading this page, the same content will reappear in the form.

This view class inherits from ``UpdateView``, which is responsible for displaying the form and
validating the submitted data, just as we would do it using a classic Django view class. The other
three mixin classes serve the following purposes:

Add class :class:`formset.views.FormViewMixin` to a view class inheriting from one of the Django
form view classes. It is required to respond with a JsonResponse rather than a HttpResponse whenever
a form submission validates or fails.

The ``ArticleForm`` uses an incomplete ``Selectize`` widget. This means that the client must fetch
additional data from the server, whenever the user makes a lookup. In order to do that, the already
existing endpoint for the form submission is used. The class
:class:`formset.views.IncompleteSelectResponseMixin` intercepts these fetch requests, and forwards
them to the widget implementing the ``Selectize`` widget. By doing so, we don't have to specify any
additional endpoint for these lookups.

The ``ArticleForm`` implements a file upload field. File uploads are handled asynchronous, which
means that the payload is uploaded before the form is submitted. The class
:class:`formset.views.FileUploadMixin` intercepts these file uploads, stores them to a temporary
location and returns a signed handle, so that whenever the form is submitted, that file can be moved
to its final destination.


Complete CRUD View
==================

In a CRUD_ application, we usually add a Django View to add, update and delete an instance of our
model. The Django documentation proposes to `create one view for each of these tasks`_, a
``CreateView``, an ``UpdateView`` and a ``DeleteView`` and add routes to each of them using the URL
patterns.

.. _CRUD: https://en.wikipedia.org/wiki/Create,_read,_update_and_delete
.. _create one view for each of these tasks: https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#generic-editing-views

With **django-formset** we instead can combine them into one view class. This is because we can add
extra context data to the form's control buttons. This additional data then is submitted together
with the form's payload and can be used to distinguish between create, update and delete.

As an example let's use a simpler model, offering just one editable field:

.. code-block:: python

	class Annotation(models.Model):
	    content = models.CharField(max_length=200)

The form and view classes required to edit this model then may look something like this:

.. django-view:: annotation
	:view-function: type('AnnotationEditView', (SessionModelFormViewMixin, model_forms.AnnotationEditView), {}).as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'annotation-result'}, form_kwargs={'auto_id': 'ano_id_%s'})
	:hide-view:

	from django.http.response import JsonResponse 
	from testapp.models.annotation import Annotation

	class AnnotationForm(ModelForm):
	    class Meta:
	        model = Annotation
	        fields = '__all__'

	class AnnotationEditView(FormViewMixin, UpdateView):
	    model = Annotation
	    form_class = AnnotationForm
	    template_name = 'crud-form.html'
	    success_url = '/success'

	    def get_context_data(self, **kwargs):
	        context_data = super().get_context_data(**kwargs)
	        if self.object:
	            context_data['change'] = True
	        else:
	            context_data['add'] = True
	        return context_data

	    def form_valid(self, form):
	        if extra_data := self.get_extra_data():
	            if extra_data.get('add') is True:
	                form.instance.save()
	            if extra_data.get('delete') is True:
	                form.instance.delete()
	                return JsonResponse({'success_url': self.get_success_url()})
	        return super().form_valid(form)

In method ``get_context_data`` we determine, whether a new object shall be added or an existing
object shall be changed. This context data then is added to the rendering context and the view then
is rendered by a template with button settings, depending on these values:

.. code-block:: django
	:caption: crud-form.html

	<django-formset endpoint="{{ request.path }}" csrf-token="{{ csrf_token }}">
	  {% render_form form %}
	  {% if add %}
	    <button type="button" df-click="submit({add: true}) -> proceed">{% trans "Add" %}</button>
	  {% else %}
	    <button type="button" df-click="submit({update: true}) -> proceed">{% trans "Update" %}</button>
	    <button type="button" df-click="submit({delete: true}) -> proceed">{% trans "Delete" %}</button>
	  {% endif %}
	</django-formset>

Method ``form_valid`` is called by Django, after a form has been validated in order to save its
cleaned data. Here we examine the extra data submitted together with the form's payload. In the
form template from above, the submit buttons "Add", "Update" and "Delete" do pass extra data
together with the submitted form data, using the ``submit()`` action when the corresponding button
is clicked. We use that extra information in our view to distinguish between creating, updating or
deleting an instance. 

.. django-referred-view:: annotation

In a real world application, this above example is oversimplified. Normally, one has to distinguish
between an add view and various details views using a unique key as identifier. If the above view 
would be connected to a URL router, the patterns may be defined as:

.. code-block:: python

	urlpatterns = [
	    ...
	    path('', AnnotationEditView.as_view(),  # list view not handled here
	        name='list-annotation'
	    ),
	    path('add/', AnnotationEditView.as_view(extra_context={'add': True}),
	        name='add-annotation',
	    ),
	    path('<int:pk>/', AnnotationEditView.as_view(extra_context={'change': True}),
	        name='change-annotation',
	    ),
	    ...
	]

In the view class itself, the two methods ``get_object()`` and ``get_success_url()`` must be adopted
as well. Here it's up to the developer to decide how the workflow should look like, after an object
has been successfully saved.

.. code-block:: python

	class AnnotationEditView(FormViewMixin, UpdateView):
	    ...
	    extra_context = None

	    def get_object(self, queryset=None):
	        if queryset is None:
	            queryset = self.get_queryset()
	        # use `querset` and `self.form_kwargs` to find the object to change
	        ...

	    def get_success_url():
	        if extra_data := self.get_extra_data():
	            # use `extra_data` to determine the success_url
	            ...

In a real world application, please remember to check if the current user has proper add-, change-
and delete permissions. The Django views running inside this documentation use the session-ID to
assign saved objects to their users.

.. note:: The list view is not handled explicitly here, because it doesn't differ compared to a
	classic Django view.
