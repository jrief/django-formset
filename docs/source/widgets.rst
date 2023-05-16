.. _widgets:

===================
Alternative Widgets
===================

.. rubric:: Replacing Widgets for Choice Fields

These widgets are the :class:`formset.widget.Selectize`, :class:`formset.widget.SelectizeMultiple`,
and :class:`formset.widget.DualSelector`. They shall be used as a replacement for the default
widgets offered by Django. This can be done by mapping the named fields to alternative widgets
inside the form's ``Meta`` class:

.. code-block:: python

	from formset.widgets import DualSelector, Selectize, SelectizeMultiple

	class ArticleForm(ModelForm):
	    class Meta:
	        ...
	        widgets = {
	            'reporter': Selectize(search_lookup='full_name__icontains'),
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

.. code-block:: python

	from formset.widgets import UploadFileInput

	class ArticleForm(ModelForm):
	    class Meta:
	        ...
	        widgets = {
	            'teaser': UploadFileInput(),
	            ...
	        }


.. rubric:: Replacing Widget for TextField

In case we want to offer a widget to :ref:`richtext` but prefer to use the model field
``django.db.models.TextField``, we have to map this widget in the ``Meta`` class of the form
class instantiating the model.

.. code-block:: python

	from formset.richtext.widgets import RichTextarea

	class ArticleForm(ModelForm):
	    class Meta:
	        ...
	        widgets = {
	            'content': RichTextarea(),
	            ...
	        }

Usually you don't want to use the default control elements for that rich text editor, but instead
configure your own preferences.

The model field :class:`formset.richtext.fields.RichTextField` maps to widget ``RichTextarea`` by
default, but again you may prefer to use your own configuration of control elements and hence you
have to map the widget in the ``Meta`` class of the form class instantiating the model.


.. rubric:: Replacing Widget for Date- and DateTime Fields

These widgets are the :class:`formset.widget.DateInput`, :class:`formset.widget.DateTimeInput`,
:class:`formset.widget.DatePicker` and :class:`formset.widget.DateTimePicker`.

Django by default uses a field such as ``<input type="text" …>`` to accept dates as input. This
means that the conversion from a string in potentially different formats, must be done by Django
itself. Modern browsers however offer input fields of type ``date`` and ``datetime-local``. There
the value is *always* submitted using the ISO format, avoiding ambiguities.
