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


.. rubric:: Separator

The class :class:`formset.richtext.controls.Separator` has no functional purpose. It can be used
to separate the other buttons visually using a vertical bar.


.. rubric:: Group

The class :class:`formset.richtext.controls.Group` is just a wrapper and can be used to group other
control elements. Each group shows a vertical bar for visual separation unless it isn't the last
entry in the current line. It hence can be used to group buttons which belong together. If the group
does not fit into the menu bar, it wraps altogether to the next line.


.. rubric:: FontFamily

The class :class:`formset.richtext.controls.FontFamily` can be used to change the font family of
the selected text. It must be initialized with a list of two-tuples, containing the CSS class as its
first element and a label as its second element. The ``FontFamily`` is based on the
``ClassBaseControlElement`` control element – check below for details.


.. rubric:: FontSize

The class :class:`formset.richtext.controls.FontSize` can be used to change the font size of the
selected text. It also is based on the ``ClassBaseControlElement`` control element and must be
initialized with a list of two-tuples.


.. rubric:: LineHeight

The class :class:`formset.richtext.controls.LineHeight` can be used to change the line height of the
current paragraph. It also is based on the ``ClassBaseControlElement`` control element and must be
initialized with a list of two-tuples.


Generic Control Elements
------------------------

TipTap offers a wide range of formatting options, which can be added to the editor. For customized
extensions, one however must provide their own `extension class written in JavaScript
<https://tiptap.dev/docs/editor/extensions/custom-extensions>`_.

When creating a control element for the RichtextArea, we often just need to provide a set of CSS
classes which can be used to style some text. The chosen CSS class out of this set of options then
is applied to the selected text, resulting in a ``<span class="…">styled text</span>``-element.

For Django developers it would be very tedious to write a JavaScript extension for each of these
formatting options. Therefore **django-formset** offers a generic control element, which can be
configured using a list of CSS classes. This control element then adds a drop down menu to the
editor's toolbar and allows the user to select one of the provided classes, which in turn are
applied to the selected text.

As an example, assume that we want to be able apply special styling to some text, for instance to
mark it. We then can create a control element such as:

.. code-block:: python

	from formset.richtext.controls import ClassBaseControlElement

	class MarkControl(ClassBaseControlElement):
	    extension = 'markText'
	    label = _("Mark Text")

The attribute ``extension`` must be a unique identifier for this control element. The attribute
``label`` is a human readable string which will be shown as the button's tooltip. In addition, we
may provide a symbol rendered in the button by specifying the attribute
``icon = 'path/to/mark-icon.svg.'``.

When declaring the ``RichtextArea`` widget, we then can add this custom control element to our list
of control elements:

.. code-block:: python

	class BlogForm(forms.Form):
	    text = fields.CharField(widget=RichTextarea(control_elements=[
	        ...
	        MarkControl({
	            'text-red': "Red",
	            'text-green': "Green",
	            'text-blue': "Blue",
	        }),
	        ...
	    ])

Now, when the user selects some text and clicks on the button labeled "Mark Text", a drop down menu
will appear, offering the options "Default", "Red", "Green" and "Blue". When selecting one of these
options, a span element with the selected CSS class will be wrapped around the selected text. The
item labeled "Default" will remove the CSS class from the selected text.

.. note:: When implementing this, do not forget to declare the named CSS classes in its CSS file.

A variant of the above control element is, when the CSS shall not be applied to the selected text,
but to a whole block. This can be achieved by adding the member ``extension_type = 'node'`` to the
class inheriting from ``ClassBaseControlElement``. The control element ``LineHeight`` (see above)
is an example for this.


Composed Formatting Options
---------------------------

In addition to the simple formatting options, **django-formset** offer some control elements which
require multiple parameters. They use the class :class:`formset.richtext.controls.DialogControl`,
which when clicked opens a :ref:`Dialog Form <dialog-forms>`. As its only argument, it takes an
instance of a dialog form. Check the possible options below:

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


.. rubric:: use_json

If the content of the rich text editor shall be stored as JSON, set ``use_json=True``. This only is
required when using this widget for a Django form's ``CharField``. When using the model field class
:class:`formset.richtext.models.fields.RichTextField`, this is not necessary.

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

Always keep in mind that storing HTML provides by arbitrary users is a potential security risk. When
rendering this HTML, it is important to sanitize it using a library such as `django-nh3`_. Moreover,
do not forget to mark the content as safe text, when rendering it inside a Django template.

.. _django-nh3: https://pypi.org/project/django-nh3/

If the content of such a field shall be rendered inside a Django template, do not forget to mark
it as "safe", either by using the function `django.utils.safestring.mark_safe`_ or by using the
template filter `{{ …|safe }}`_.

.. _django.utils.safestring.mark_safe: https://docs.djangoproject.com/en/stable/ref/utils/#django.utils.safestring.mark_safe
.. _{{ …|safe }}: https://docs.djangoproject.com/en/4.1/ref/templates/builtins/#safe

While this is a quick and fast solution, we shall always keep in mind that storing plain HTML inside
a database field, prevents us from transforming the stored information into the final format while
rendering. This means that the stored HTML is rendered as-is. A better and more secure alternative
is to store that data as JSON.


Storing rich text as JSON
-------------------------

Since HTML content has an implicit tree structure, an alternative approach to HTML is to keep this
hierarchy unaltered when storing. The best suited format for this is JSON. This approach has the
advantage that HTML is rendered during runtime, allowing to adopt the result as needed. It also does
not require to sanitize the content, because the JSON structure is only converted to HTML tags
allowed by the implementation.

**django-formset** provides a special model field class
:class:`formset.richtext.models.fields.RichTextField`. It shall be used as a replacement to Django's
model field class ``TextField``. This model field provides the widget ``RichTextarea`` using the
default settings. Often that might not be the desired configuration, and it may be necessary to
re-declare that widget, while creating the form from the model.

In this example we use a model with one field for storing the rich text entered by the user:

.. code-block:: python
	:caption: models.py

	from django.db.models import Model
	from formset.richtext.models.fields import RichTextField
	
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
	            'body': RichTextarea(
	                control_elements=[
	                    controls.Heading([1,2,3]),
	                    controls.Bold(),
	                    controls.Blockquote(),
	                    controls.CodeBlock(),
	                    controls.HardBreak(),
	                    controls.Italic(),
	                    controls.Underline(),
	                    controls.TextColor([
	                        'rgb(212, 0, 0)',
	                        'rgb(0, 212, 0)',
	                        'rgb(0, 0, 212)',
	                    ]),
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
	                ],
	                attrs={
	                    'placeholder': "Start typing …",
	                    'maxlength': 2000
	                },
	            ),
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
