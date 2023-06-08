.. _alternative-widgets:

===================
Alternative Widgets
===================

**django-formset** ships with a set of alternative widgets for various purposes. This is because
Django, out of the box, only supports pure HTML input fields which, from a usability point of view,
are not that convenient nowadays. To fill this gap, many JavaScript frameworks offer better suited
widgets, but they usually require writing extra client code, contradicting the DRY principle.

Many alternative widgets have to communicate with a server endpoint in order to fetch additional
data. This is the reason why some of the views require a mixin class to handle that extra endpoint.
Therefore with **django-formset** the developer can completely focus on the server side. Here is
a of currently implemented widgets:


Widgets for Choice Fields
=========================

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
the ``<select>`` and ``<select multiple="multiple">`` widgets. Views implementing these widgets
must inherit from :class:`formset.views.IncompleteSelectResponseMixin`.


Widgets for File- and Image Fields
==================================

In case we want to map a model field of type ``django.db.models.FileField`` or
``django.db.models.ImageField``, we **must** replace the default input widget by
``formset.widgets.UploadedFileInput``. This is required because in **django-formset** files are
*uploaded before* form submission. Please read the section :ref:`uploading` for details about file
uploading. Views implementing this widgets must inherit from
:class:`formset.upload.FileUploadMixin`.

.. code-block:: python

	from formset.widgets import UploadFileInput

	class ArticleForm(ModelForm):
	    class Meta:
	        ...
	        widgets = {
	            'teaser': UploadFileInput(),
	            ...
	        }


Widget for TextField
====================

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


Widgets for Date- and DateTime Fields
=====================================

Django by default uses a field such as ``<input type="text" …>`` to accept dates as input. This
means that the conversion from a string in potentially different formats, must be done by Django
itself. Modern browsers however offer input fields such as ``<input … type="date">`` and
``<input … type="datetime-local">``, and implement their own date- and datetime-pickers. Whenever a
value is submitted from these widgets, it *always* uses the ISO format. Django instead allows
different date- and datetime formats, and this can lead to ambiguities.

These widgets can be imported from :class:`formset.widget.DateInput` and
:class:`formset.widget.DateTimeInput`

In addition to these two widgets **django-formset** offers two more alternatives, namely
:class:`formset.widget.DatePicker` and :class:`formset.widget.DateTimePicker`.

In some situations, developers might want to use their own HTML representation and styles for
date- and datetime-pickers. Since those calendar sheets are rendered by Django, developers have
full control over the rendering of those widgets and can even use their own context to add
additional information.

Please read the section :ref:`calendar` on details about these two alternative widgets. Views
implementing the latter, must inherit from :class:`formset.calendar.CalendarResponseMixin`.
