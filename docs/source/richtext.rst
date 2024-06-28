.. _richtext:

=============
Edit Richtext
=============

A ``RichTextarea`` allows editing or pasting formatted text, similar to traditional "What you see is
what you get" (WYSIWYG) editors. The current implementation offers common text formatting options
such as paragraphs, headings, emphasized and bold text, ordered and bulleted lists, and hyperlinks.
More text formatting options will be implemented in the future.

The **django-formset** library provides a widget, which can be used as a drop-in replacement for the
HTML element ``<textarea>``, implemented as a web component. In a Django form's ``CharField``, we
just have to replace the built-in widget against :class:`formset.richtext.widgets.RichTextarea`.

.. django-view:: blog_form

	from django.forms import fields, forms
	from formset.richtext.widgets import RichTextarea

	class BlogForm(forms.Form):
	    text = fields.CharField(widget=RichTextarea)

This widget can be configured in various ways in order to specifically enable the currently
implemented formatting options. With the default settings, this textarea will show up like:

.. django-view:: blog_view
	:view-function: BlogView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'blog-result'}, form_kwargs={'auto_id': 'bl_id_%s'})
	:hide-code:

	from formset.views import FormView 

	class BlogView(FormView):
	    form_class = BlogForm
	    template_name = "form.html"
	    success_url = "/success"


Configuration
=============

When offering a rich textarea, the default formatting options may not be appropriate. Therefore,
the widget class ``RichTextarea`` can be configured using various control elements.

.. code-block:: python

	from formset.richtext import controls
	from formset.richtext.widgets RichTextarea

	richtext_widget = RichTextarea(control_elements=[
	    controls.Bold(),
	    controls.Italic(),
	])

This configuration would only allow to format text using **bold** and *italic*. Currently
**django-formset** implements these formatting options:


Simple Formatting Options
-------------------------

.. rubric:: Heading

The class :class:`formset.richtext.controls.Heading` can itself be configured using a list of levels
from 1 through 6. ``Heading([1, 2, 3])`` allows for instance, to format a heading by using the HTML
tags ``<h1>``,  ``<h2>`` and  ``<h3>``. If provided without parameters, all 6 possible heading
levels are available. If only one level is provided, for instance as ``Heading(1)``, then the
heading button does not provide a pull down menu, but instead is rendered as a single **H1** button.
This allows placing heading buttons for different levels on the toolbar side by side.


.. rubric:: Bold

The class :class:`formset.richtext.controls.Bold` can be used to format a selected part of the text
in bold variant of the font. It can't be further configured.


.. rubric:: Italic

The class :class:`formset.richtext.controls.Italic` can be used to format a selected part of the
text in an emphasized (italic) variant of the font. It can't be further configured.


.. rubric:: Underline

The class :class:`formset.richtext.controls.Underline` can be used to format a selected part of the
text as underlined. This option rarely makes sense. It can't be further configured.


.. rubric:: BulletList

The class :class:`formset.richtext.controls.BulletList` can be used to format some text as a
bulleted list. It can't be further configured.


.. rubric:: OrderedList

The class :class:`formset.richtext.controls.OrderedList` can be used to format some text as ordered
(ie. numbered) list. It can't be further configured.


.. rubric:: HorizontalRule

The class :class:`formset.richtext.controls.HorizontalRule` can be used to add a horizontal rule
between paragraphs of text. It can't be further configured.


.. rubric:: Clear Format

The class :class:`formset.richtext.controls.ClearFormat` can be used to remove the current format
settings of selected text. It can't be further configured.


.. rubric:: Undo and Redo

The classes :class:`formset.richtext.controls.Undo` and :class:`formset.richtext.controls.Redo` can
be used to undo and redo changes on the current text. They can't be further configured.


.. rubric:: Subscript

The class :class:`formset.richtext.controls.Subscript` can be used to mark text as subscript, which
renders the selected text smaller and below the baseline.


.. rubric:: Superscript

The class :class:`formset.richtext.controls.Superscript` can be used to mark text as superscript,
which renders the selected text smaller and above the baseline.


.. rubric:: Separator

The class :class:`formset.richtext.controls.Separator` has no functional purpose. It can be used
to separate the other buttons visually using a vertical bar.


.. rubric:: Text Align

The class :class:`formset.richtext.controls.TextAlign` can be used to align a block of text. It must
be initialized as

.. code-block:: python

	TextAlign(['left', 'center', 'right', 'justify])

this will create a drop down menu offering these three options. As an alternative one can for
instance use

.. code-block:: python

	TextAlign('right')

which creates a single button to align the selectd text box to the right.


.. rubric:: Text Color

The class :class:`formset.richtext.controls.TextColor` can be used to mark text in different colors.
It offers two different modes: Styles and CSS classes. When used with styles, the control element
must be initialized with colors in rgb format, for instance:

.. code-block:: python

    TextColor(['rgb(255, 0, 0)', 'rgb(0, 255, 0)', 'rgb(0, 0, 255)']) 

This will offer text in three colors, red, green and blue. When used with classes, the control
element must be initialized with arbitrary CSS classes, for instance

.. code-block:: python

	TextColor(['text-red', 'text-green', 'text-blue']) 

The implementor then is responsible for setting the text color in its CSS file for these classes.
Style- and class-based initialization can not be interchanged.


.. rubric:: Text Indent

The class :class:`formset.richtext.controls.TextIndent` can be used to indent and outdent the first
line of a text block. It must be initialized as

.. code-block:: python

    TextIndent('indent')  # to indent the first line
    TextIndent('outdent')  # to indent all but the first line 


.. rubric:: Text Margin

The class :class:`formset.richtext.controls.TextMargin` can be used to indent and dedent a text
block. It must be initialized as

.. code-block:: python

    TextMargin('increase')  # to increase the left margin
    TextIndent('decrease')  # to decrease the left margin 


.. rubric:: Blockquote

The class :class:`formset.richtext.controls.Blockquote` can be used to mark a text block as quoted
by adding a thick border on its left.


.. rubric:: Code Block

The class :class:`formset.richtext.controls.CodeBlock` can be used to mark a text block as a code
block. This is useful to show samples of code.


.. rubric:: Hard Break

The class :class:`formset.richtext.controls.Hardbreak` can be used to add a hard break to a
paragraph, ie. add a ``<br>`` to the rendered HTML.


Composed Formatting Options
---------------------------

In addition to the simple formatting options, **django-formset** offer some control elements which
require multiple parameters. They use the class :class:`formset.richtext.controls.DialogControl`,
which when clicked opens a :ref:`dialog-form`. As its only argument, it takes an instance of a
dialog form. Check the possible options below:

Here are the built-in dialog forms:

.. rubric:: Link

The class :class:`formset.richtext.dialog.SimpleLinkDialogForm` can be used to add a hyperlink to a
selected part of some text. When choosing this option, a dialog pops up and the user can enter a
URL and edit the selected text.

To declare this control write:

.. code-block:: python

	from formset.richtext.controls import DialogControl
	from formset.richtext.dialogs import SimpleLinkDialogForm

	DialogControl(SimpleLinkDialogForm())

The form is named ``SimpleLinkDialogForm`` because it only allows to enter a URL. The users of this
rich text field might however want to edit hyperlinks with the ``ref`` and ``target`` attributes,
and might also want to set links on Django models providing the method `get_absolute_url`_, but
referring to the primary key of the provided object. Since there can't be any one-size-fits-all
solution, it is the implementor responsibility to provide a custom dialog form for this purpose.
Section :ref:`richtext-extensions` explains in detail how to do this.

.. _get_absolute_url: https://docs.djangoproject.com/en/stable/ref/models/instances/#get-absolute-url


.. rubric:: Footnote

An instance of the class :class:`formset.richtext.dialog.FootnoteDialogForm` can be used to add a
footnote editor to the editable rich text. When choosing this option, a dialog pops up with another
richtext editor inside. This editor can be configured in the same way as the main editor, but
usually one would only allow very few formatting options. The content of this editor will be stored
as a footnote and is not visible in the main text area. Instead, only a ``[*]`` will be rendered.

This control element only works if the editor's payload is stored as JSON. Reason is that the
richtext renderer adds them to the end of the document in a second run. Check for details below.


.. rubric:: Image

The class :class:`formset.richtext.dialog.SimpleImageDialogForm` can be used to add an image to the
editable rich text. When choosing this option, a dialog pops up and the user can drag an image into
the upload field. It will be uploaded to the server and only a reference to this image will be
stored inside the text. The form is named ``SimpleImageDialogForm`` because it only allows to upload
an image. The users of this rich text field might however want to edit the image size, the alt text,
the caption, the alignment and other custom fields. Since there can't be any one-size-fits-all
solution, it is the implementor responsibility to provide a custom dialog form for this purpose.
Therefore this dialog form can be used as a starting point for a custom image uploading dialog form.


.. rubric:: Placeholder

The class :class:`formset.richtext.dialog.PlaceholderDialogForm` can be used to add a placeholder to
the selected part of some text. When choosing this option, a dialog pops up and the user can enter a
variable name and edit the selected placeholder text. Such a control element can be used to store
HTML with contextual information. When this HTML content is finally rendered, those placeholder
entries can be replaced against some context using the built-in Django template rendering functions.

.. note:: Internally the placeholder extension is named "procurator" to avoid a naming conflict,
	because there is a built-in TipTap extension named "placeholder".


Additional Attributes
---------------------

Apart from the control elements, the rich text editor widget can be configured using additional
attributes:

.. rubric:: maxlength

By adding ``maxlength`` to the widget's attributes, we can limit the number of characters to be
entered into this text field. In the bottom right corner, this will show how many characters can
still be entered.


.. rubric:: placeholder

By adding ``placeholder="Some text"`` to the widget's attributes, we can add a placeholder to the
text field. This will disappear as soon as we start typing.


Richtext as a Model Field
=========================

In the example from above, we used a Django form ``CharField`` and replaced the default widget
provided by Django (``TextInput``). A more common use case is to store the entered rich text in
a database field. Here **django-formset** offers two solutions:


Storing rich text as HTML
-------------------------

Storing rich text as HTML inside the database using the field `django.db.models.fields.TextField`_  
is the simplest solution. It however requires to override the default widget (``Textarea``) against
the ``RichTextarea`` provided by **django-formset**, when instantiating the form associated with
this model.

.. _django.db.models.fields.TextField: https://docs.djangoproject.com/en/stable/ref/models/fields/#textfield

If the content of such a field shall be rendered inside a Django template, do not forget to mark
it as "safe", either by using the function `django.utils.safestring.mark_safe`_ or by using the
template filter `{{ …|safe }}`_.

.. _django.utils.safestring.mark_safe: https://docs.djangoproject.com/en/stable/ref/utils/#django.utils.safestring.mark_safe
.. _{{ …|safe }}: https://docs.djangoproject.com/en/4.1/ref/templates/builtins/#safe

While this is a quick and fast solution, we shall always keep in mind that storing plain HTML inside
a database field, prevents us from transforming the stored information into the final format while
rendering. This means that the stored HTML is rendered as-is. A better alternative is to store that
data as JSON.


Storing rich text as JSON
-------------------------

Since HTML content has an implicit tree structure, an alternative approach to HTML is to keep this
hierarchy unaltered when storing. The best suited format for this is JSON. This approach has the
advantage that HTML is rendered during runtime, allowing to adopt the result as needed.

**django-formset** provides a special model field class
:class:`formset.richtext.fields.RichTextField`. It shall be used as a replacement to Django's model
field class ``TextField``. This model field provides the widget ``RichTextarea`` using the default
settings. Often that might not be the desired configuration, and it may be necessary to re-declare
that widget, while creating the form from the model.

In this example we use a model with one field for storing the rich text entered by the user:

.. code-block:: python
	:caption: models.py

	from django.db.models import Model
	from formset.richtext.fields import RichTextField
	
	class BlogModel(Model):
	    body = RichTextField()

We then use that model to create a Django ModelForm. For demonstration purposes we configure all
available control elements. Such a configured editor then will look like: 

.. django-view:: editor_form
	:caption: forms.py

	from django.forms.models import ModelForm
	from formset.richtext import controls
	from formset.richtext import dialogs
	from testapp.models import BlogModel

	class EditorForm(ModelForm):
	    class Meta:
	        model = BlogModel
	        fields = '__all__'
	        widgets = {
	            'body': RichTextarea(control_elements=[
	                controls.Heading([1,2,3]),
	                controls.Bold(),
	                controls.Blockquote(),
	                controls.CodeBlock(),
	                controls.HardBreak(),
	                controls.Italic(),
	                controls.Underline(),
	                controls.TextColor(['rgb(212, 0, 0)', 'rgb(0, 212, 0)', 'rgb(0, 0, 212)']),
	                controls.TextIndent(),
	                controls.TextIndent('outdent'),
	                controls.TextMargin('increase'),
	                controls.TextMargin('decrease'),
	                controls.TextAlign(['left', 'center', 'right']),
	                controls.HorizontalRule(),
	                controls.Subscript(),
	                controls.Superscript(),
	                controls.DialogControl(dialogs.SimpleLinkDialogForm()),
	                controls.DialogControl(dialogs.PlaceholderDialogForm()),
	                controls.DialogControl(dialogs.FootnoteDialogForm()),
	                controls.Separator(),
	                controls.ClearFormat(),
	                controls.Redo(),
	                controls.Undo(),
	            ], attrs={'placeholder': "Start typing …", 'maxlength': 2000}),
	        }

.. django-view:: editor_view
	:view-function: EditorView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'editor-result'}, form_kwargs={'auto_id': 'ef_id_%s'})
	:hide-code:

	from django.views.generic import UpdateView
	from formset.views import FormViewMixin, IncompleteSelectResponseMixin
	from testapp.demo_helpers import SessionModelFormViewMixin

	class EditorView(SessionModelFormViewMixin, FormViewMixin, UpdateView):
	    model = BlogModel
	    form_class = EditorForm
	    template_name = 'form.html'
	    success_url = '/success'

.. note:: After submission, the content of this form is stored in the database. Therefore after
	reloading this page, the same content will reappear in the form.


.. _rendering-richtext:

Rendering Richtext
------------------

Since the editor's content is stored in JSON, it must be converted to HTML before being rendered.
For this purpose **django-formset** offers a templatetag, which can be used such as:

.. code-block:: django

	{% load richtext %}
	
	{% render_richtext obj.body %}

Here ``obj`` is a Django model instance with the field ``body`` of type ``RichTextField``.


Overriding the Renderer
-----------------------

By postponing the conversion from JSON to a readable format, we can keep our document structure
until it is rendered. **django-formset** provides default templates for this conversion, but you may
want to use your own ones:

.. code-block:: django

	{% load richtext %}
	
	{% render_richtext obj.content "path/to/alternative/doc.html" %}

The template ``doc.html`` is the starting point for each document. Looking at the structure of a
rich text document stored in JSON, we see the hierachical structure:

.. code-block:: json

	{
	    "text": {
	        "type": "doc",
	        "content": [{
	            "type": "paragraph",
	            "content": [{
	                "type": "text",
	                "text": "This is "
	            }, {
	                "type": "text",
	                "marks": [{
	                    "type": "bold"
	                }],
	                "text": "bold"
	            }, {
	                "type": "text",
	                "text": " "
	            }, {
	                "type": "text",
	                "marks": [{
	                    "type": "italic"
	                }],
	                "text": "and italic"
	            }, {
	                "type": "text",
	                "text": " text."
	            }]
	        }]
	    }
	}

The ``type`` determines the template to use, whereas ``content`` is a list of nodes, rendered using
their own sub-template determined by their own ``type``.

When rendered by the default ``richtext/doc.html`` template, its output looks like:

.. code-block:: html

	<p>This is <strong>bold</strong> <em>and italic</em> text.</p> 


Implementation Details
======================

This Richtext editing widget is based on the `headless Tiptap editor`_. This framework offers many
more formatting options than currently implemented by the **django-formset** library. In the near
future I will add them in a similar way to the existing control elements. Please help me to
implement them by contributing to this project.

.. _headless Tiptap editor: https://tiptap.dev/

With Tiptap it even is possible to create application specific control elements, which thanks to the
internal JSON structure, then can be transformed to any imaginable HTML.
