.. _model-form:

==========================
Creating Forms from Models
==========================

Just as in Django, forms can be created from models and rendered by **django-formset**.  

Say, we use the same model as described in the Django documentation, ie. ``myapp.models.Article``,
then we use that model to create a form class, for example:

.. code-block:: python

	class ArticleForm(ModelForm):
	    class Meta:
	        model = Article
	        fields = ['pub_date', 'headline', 'content', 'reporter']

There however is a caveat here: **django-formset** offers some widgets, which greatly enhance the
functionality of some input elements, compared to their pure HTML counterpart.


.. rubric:: Replacing Widgets for Choice Fields

These widgets are the :class:`formset.widget.Selectize`, :class:`formset.widget.SelectizeMultiple`,
and :class:`formset.widget.DualSelector`. They shall be used as a replacement to default widgets
offered by Django. This can be done by mapping the named fields to alternative widgets inside the
form's ``Meta`` class:

.. code-block:: python

	from formset.widgets import DualSelector, Selectize, SelectizeMultiple

	class ArticleForm(ModelForm):
	    class Meta:
	        ...
	        widgets = {
	            'single_choice': Selectize,
	            'multiple_choice': SelectizeMultiple,  # or DualSelector
	            ...
	        }

Please read the sections :ref:`selectize` and :ref:`dual-selector` for details about enhancing
the ``<select>`` and ``<select multiple="multiple">`` widgets.


.. rubric:: Replacing Widgets for File- and Image Fields

In case we want to map a model field of type ``django.db.models.FileField`` or
``django.db.models.ImageField``, we **must** replace the default input widget by
``formset.widgets.UploadedFileInput``. This is required because in **django-formset** files are
*uploaded before* form submission. Please read the section :ref:`uploading` for details about file
uploading.


Detail View for ModelForm
=========================

In a CRUD_ application, we usually add a Django View to add, update and delete an instance of our
model. Instead of `createing one view class`_ for each of those operations, with **django-formset**
we usually can combine them into one view class. This is because we can add extra context data to
the form control buttons, which then is sumbitted together with the form data. An example:

.. _CRUD: https://en.wikipedia.org/wiki/Create,_read,_update_and_delete
.. _createing one view class: https://docs.djangoproject.com/en/stable/ref/class-based-views/generic-editing/#generic-editing-views


.. code-block:: python

	from django.contrib.auth.mixins import LoginRequiredMixin
	from django.views.generic import UpdateView
	from formset.views import FileUploadMixin, FormViewMixin

	class ArticleEditView(FileUploadMixin, FormViewMixin, LoginRequiredMixin, UpdateView):
	    model = Article
	    template_name = 'myapp/edit-form.html'
	    form_class = ArticleForm
	    success_url = reverse_lazy('address-list')  # or whatever makes sense
	    extra_context = None

	    def get_object(self, queryset=None):
	        if self.extra_context['add'] is False:
	            return super().get_object(queryset)

	    def form_valid(self, form):
	        if extra_data := self.get_extra_data():
	            if extra_data.get('delete') is True:
	                self.object.delete()
	                success_url = self.get_success_url()
	                response_data = {'success_url': force_str(success_url)} if success_url else {}
	                return JsonResponse(response_data)
	        return super().form_valid(form)

We now must adopt the template used to render the edit form

.. code-block:: django

	<django-formset endpoint="{{ request.path }}">
	    {% render_form form %}
	    {% if add %}
	    <button type="button" click="submit({add: true}) -> proceed">{% trans "Add" %}</button>
	    {% else %}
	    <button type="button" click="submit({update: true}) -> proceed">{% trans "Update" %}</button>
	    <button type="button" click="submit({delete: true}) -> proceed">{% trans "Delete" %}</button>
	    {% endif %}
	</django-formset>

The interesting part here is that we use the context variable ``add`` to distinguish between the
Add- and the Update/Delete-Views. This context variable is added using the ``extra_context``
parameter, see below.

Additionally the submit buttons "Add", "Update" and "Delete" have the ability to pass some extra
data together with the submitted form data. We use that information in the ``form_valid``-method in
our view to distinguish between the creation, the update or the deletion of an instance, see above. 

Finally we must attach that view class to our URL routing. Here we reuse our form view class
``ArticleEditView`` and use the parameter ``extra_context`` to modify the behaviour of that view.

.. code-block:: python

	urlpatterns = [
	    ...
	    urlpatterns = [
	    path('', AddressListView.as_view(), name='address-list'),  # list view not handled here 
	    path('add/', ArticleEditView.as_view(extra_context={'add': True}),
	        name='address-add',
	    ),
	    path('<int:pk>/', ArticleEditView.as_view(extra_context={'add': False}),
	        name='address-edit',
	    ),
	    ...
	]

.. note:: The list view is not handled explicitly here, because it doesn't differ compared to a
	classic Django view.
