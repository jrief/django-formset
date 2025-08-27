.. _richtext-extensions:

===================
Richtext Extensions
===================

.. versionadded:: 1.4

Having a Richtext editor which can set simple property values such as **bold** or *italic* on
editable text elements is not a big deal, even the most basic implementation can do that. The
difficulty arises when you want to set more than one property on a certain paragraph or node.

Take for instance the hyperlink, the most basic implementation requires two fields: the URL and the
text to display. But some implementers might want to set more properties, such as the rel_, the
target_ attribute, or they want to link onto phone numbers, email addresses or to downloadable
files. Moreover, if the Richtext editor shall be used in a content management system or an
e-commerce site, one might want to set a link to an internal CMS page or a product, in order to keep
its referential integrity. In such a dialog form, the user then can select the page or the product
out of a list of available options, instead of entering the URL to that page manually. This
requires a ModelChoiceField_, something usually not available from an off the shelf implementation.

As another example consider adding an image element to the Richtext editor. A typical ready made
solution such as TinyMCE_ would offer a file upload area and a few additional fields to set the
image's width, height and alt tags. The image's payload then often is encoded as a base64 string in
the editor's document state. So what if instead the implementer wants to store the image as a file
in its own media library and the meta-data in a separate database table? Here is where
**django-formset** offers a flexible way to create custom dialog forms and to extend the Richtext
editor with your own needs.

So the basic idea is to allow the implementer to extend the Richtext editor with custom dialog forms
based on the same principles as the built-in :ref:`dialog-forms`. This way the implementer can
combine any fields and widgets to create a dialog form which fits his exact needs. This dialog form
then can be attached to the Richtext editor as a control element, which can be used to set the
properties of a certain node or mark element.

ProseMirror_, the underlying editor framework of Tiptap, stores the document's content (state) as
a nested structure of plain JavaScript objects and arrays. Tiptap then adds its own abstractions on
top of ProseMirror and can export and import this document state as JSON. The document state
consists of nodes and marks, each of them having their own plugin type with one or more attributes.
When extending the editor, we usually create a dialog form for such a plugin type, where we can edit
the required attributes. These attributes then are stored inside the editor's document state. When
rendering the content of the editor, we can use these attributes to render the desired HTML output.

**django-formset** offers different ways to map the field values of the special dialog editors to
the document's state and vice versa. This is explained in detail in section :ref:`behind-the-scenes`
below.

.. _rel: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a#rel
.. _target: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a#target
.. _ModelChoiceField: https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.ModelChoiceField
.. _TinyMCE: https://www.tiny.cloud/docs/tinymce/latest/full-featured-open-source-demo/
.. _ProseMirror: https://prosemirror.net/


Creating a custom hyperlink editor
==================================

As we can see, there are many use cases where the implementer might want to extend the Richtext
editor with a custom dialog form adopted to his exact needs. In this example we show how to create a
custom hyperlink editor where a user can either select an external URL or an internal page for a
book from a library. The internal page is a model object of type ``PageModel`` and can be selected
using the :ref:`selectize`.

.. django-view:: pages_dialog

	from django.forms import fields, forms, models, widgets
	from formset.richtext import controls
	from formset.richtext import dialogs
	from formset.widgets import Selectize
	from formset.widgets.richtext import RichTextarea
	from testapp.models import PageModel

	class CustomHyperlinkDialogForm(dialogs.RichtextDialogForm):
	    title = "Edit Hyperlink"
	    extension = 'custom_hyperlink'
	    extension_script = 'testapp/tiptap-extensions/custom_hyperlink.js'
	    plugin_type = 'mark'
	    prefix = 'custom_hyperlink_dialog'

	    text = fields.CharField(
	        label="Link Text",
	        widget=widgets.TextInput(attrs={
	            'richtext-selection': True,
	            'size': 50,
	        })
	    )
	    link_type = fields.ChoiceField(
	        label="Link Type",
	        choices=[
	            ('external', "External URL"),
	            ('internal', "Internal Page"),
	        ],
	        initial='internal',
	        widget=widgets.Select(attrs={
	            'richtext-map-from': '{value: attributes.href ? "external" : "internal"}',
	        }),
	    )
	    url = fields.URLField(
	        label="External URL",
	        required=False,
	        widget=widgets.URLInput(attrs={
	            'size': 50,
	            'richtext-map-to': '{href: elements.link_type.value == "external" ? elements.url.value : ""}',
	            'richtext-map-from': 'href',
	            'df-show': '.link_type == "external"',
	            'df-require': '.link_type == "external"',
	            'placeholder': "https://www.example.com",
	        }),
	    )
	    page = models.ModelChoiceField(
	        queryset=PageModel.objects.all(),
	        label="Internal Page",
	        required=False,
	        widget=Selectize(attrs={
	            'richtext-map-to': '{page_id: elements.link_type.value == "internal" ? elements.page.value : ""}',
	            'richtext-map-from': 'page_id',
	            'df-show': '.link_type == "internal"',
	            'df-require': '.link_type == "internal"',
	        }),
	    )

Here we define a custom dialog form for the hyperlink editor. This dialog form has four fields,
of which ``url`` and ``page`` are mapped as parameters to the anchor element in HTML. The other two
fields are used to set the text of the link and to toggle between an internal and an external link.

Let's go through the fields one by one:

.. rubric:: The ``text`` field

This field is the text to display inside the anchor element of the link. Since the selected text in
the editor is used as the link text, we have added the attribute ``'richtext-selection': True`` to
the input field. This attribute is used by the editor to set the selected text as the initial value
of the field and vice versa.


.. rubric:: The ``link_type`` field

This choice field is used to select the type of the link, which can either be an external link
specified by an URL, or an internal link specified by the primary key of an object of type
``PageModel``. The value of this field is not stored in the Richtext editor's document state,
therefore we use a functional snippet to map the document state's value to the dialog form's field:

.. code-block:: javascript

	'richtext-map-from': '{value: attributes.href ? "external" : "internal"}'

If the ``href`` attribute of the anchor element is set, the value of this choice field is set to
"external", otherwise to "internal".


.. rubric:: The ``url`` field

This field stores the value of the external URL. We only want to set this value to the editor's
document state if the link type is set to "external", otherwise keep it empty. Therefore we use the
functional snippet:

.. code-block:: javascript

	'richtext-map-to': '{href: elements.link_type.value == "external" ? elements.url.value : ""}'

This functional snippet has access to all ``elements`` of the dialog form. Therefore we can check
for the value of the field named ``link_type`` and return the value of the field named ``url`` and
map it to the attribute ``href``.

To map the value of the editor's document state back to the dialog, we use the attribute
``'richtext-map-from': 'href'``. This takes the values from the editor's document state and applies
them to the given field.

The attribute ``'df-show': '.link_type == "external"'`` tells the editor to show this field
only if the link type is set to "external".

The attribute ``'df-require': '.link_type == "external"'`` tells the editor to make this field
optional if the link type is not set to "external". Otherwise, with link type set to "internal", the
form validation would fail, since then this field is hidden.


.. rubric:: The ``page`` field

The ``page`` field is a ModelChoiceField to select the internal page. It shall be mapped onto the
``page_id`` when stored in the editor's document state. Therefore we use the functional snippet:

.. code-block:: javascript

	'richtext-map-to': '{page_id: elements.link_type.value == "internal" ? elements.page.value : ""}'

This functional snippet has access to all ``elements`` of the dialog form. Therefore we can check
for the value of the field named ``link_type`` and return the value of the field named ``page`` and
map it to the attribute ``page_id``.

To map the value of the editor's document state back to the dialog, we use the attribute
``'richtext-map-from': 'page_id'``. This takes the values from the editor's document state and
applies them to the given field.

The attribute ``'df-show': '.link_type == "internal"'`` tells the editor to show this field
only if the link type is set to "internal".

The attribute ``'df-require': '.link_type == "internal"'`` tells the editor to make this field
optional if the link type is not set to "internal". Otherwise, with link type set to "external", the
form validation would fail, since then this field is hidden.

Finally we attach this dialog form to our ``RichTextarea`` widget by adding it to the list of
control elements:

.. django-view:: pages_form

	from django.forms import fields, forms

	class PagesForm(forms.Form):
	    text = fields.CharField(widget=RichTextarea(
	        control_elements=[
	            controls.Bold(),
	            controls.Italic(),
	            controls.DialogControl(
	                CustomHyperlinkDialogForm(),
	                icon='formset/icons/link.svg',
	            ),
	        ],
	        attrs={
	            'use_json': True,
	        },
	    ))

Apart from the custom hyperlink dialog form this editor has another two control elements, namely
Bold and Italic. They have been added for demonstration purposes only.

.. django-view:: pages_view
	:view-function: PagesView.as_view(extra_context={'framework': 'bootstrap', 'pre_id': 'page-result'}, form_kwargs={'auto_id': 'pg_id_%s'})
	:hide-code:

	from formset.views import FormView 

	class PagesView(FormView):
	    form_class = PagesForm
	    template_name = "form.html"
	    success_url = "/success"

Our form dialog ``CustomHyperlinkDialogForm`` requires additional attributes not mentioned up to
now. They are required in order to configure the Tiptap editor.


.. rubric:: The ``extension`` attribute

This is a unique identifier to register the extension within the editor. When the Tiptap editor
creates its internal representation of the edited text, this identifier is used to mark the internal
structure of the hyperlink.


.. rubric:: The ``extension_script`` attribute

This is the path to the JavaScript file which contains the implementation of the extension. This
file is loaded by the editor during runtime and must be retrievable through a static URL. Here we
specify which attributes shall be stored in the internal representation of the editor, how to render
them and how to parse HTML pasted into the editor. For details please refer to the `Tiptap
documentation on extensions`_.

.. _Tiptap documentation on extensions: https://www.tiptap.dev/api/extensions

For our custom hyperlink extension, this short JavaScript file will do the job:

.. code-block:: javascript
	:caption: myapp/tiptap-extensions/custom_hyperlink.js

	{
	    name: 'custom_hyperlink',
	    priority: 1000,
	    keepOnSplit: false,

	    addAttributes() {
	        return {
	            href: {
	                default: null,
	            },
	            page_id: {
	                default: null,
	            },
	        };
	    },

	    parseHTML() {
	        return [{tag: 'a[href]:not([href *= "javascript:" i])'}];
	    },

	    renderHTML({HTMLAttributes}) {
	        return ['a', HTMLAttributes, 0];
	    },
	}


.. rubric:: The ``plugin_type`` attribute

The attribute can be either ``'mark'`` or ``'node'``. A "mark" is a property of a text node, such
as bold or italic. A "node" is a block element, such as a paragraph or a list. For details please
refer to the Tiptap documentation on marks_ and nodes_.

.. _marks: https://www.tiptap.dev/api/marks
.. _nodes: https://www.tiptap.dev/api/nodes


.. rubric:: The ``prefix`` attribute

This attribute is another unique identifier. It is used to set a name for the dialog form.


.. _behind-the-scenes:

Behind the scenes
-----------------

The most tricky part of the implementation is the mapping of the dialog form fields to the editor's
document state and vice versa. Dialog forms therefore need a way to bidirectionally exchange their
data with the Richtext editor. This is done by adding the extra attributes ``richtext-map-to`` and
``richtext-map-from`` or ``richtext-bidirectional`` to the form field widgets.


.. rubric:: ``richtext-map-to``

This extra attribute is used to map the value of one or more form field's values to the editor's
document state. This operation is performed whenever the user clicks on the "Apply" button of the
dialog form. This attribute can take three types of values:

* **A key value**: This is used to map the value of the given field onto to the editor's document
  state with that key. This is the most basic way to map a field's value and can only be used to map
  a single value.
* **A functional expression**: This is used to map multiple field values to the editor's document
  state using a JavaScript lambda function. This snippet has access to all elements of the dialog
  form and must return a value to be mapped onto the editor's document state. Accessing the values
  of the elements can only be achieved using ``elements.…`` inside this snippet. This is a more
  flexible way, because it can take the values of other fields into account, transform them or
  perform extra logic.
  
  Example: ``{src: JSON.parse(elements.image.dataset.fileupload).download_url}`` maps the download
  URL of an uploaded image of an input element named ``image`` to the attribute ``src`` of the
  editor's document state implementing the mark extension ``<img src="…" />``.
* **The name of a function followed by empty brackets**, for instance ``image_to_document()``. This
  function must be an attribute of the object declared inside the extension script as explained in
  the previous section. It takes an HTMLFormControlsCollection_ as its only argument. This
  collection contains all the fields of the given dialog form. The function must return a plain
  JavaScript object which then is merged into the editor's document state. This is the most flexible
  way, because it can be programmed in JavaScript.

.. _HTMLFormControlsCollection: https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormControlsCollection

  .. code-block:: javascript
	:caption: myapp/tiptap-extensions/simple_image.js

	{
	    ...
	    
	    image_to_document(elements) {
	        const fileupload = JSON.parse(elements.image.dataset.fileupload);
	        return {
	            src: fileupload.download_url,
	            dataset: fileupload,
	       };
	    },
	    
	    ...
	}



.. rubric:: ``richtext-map-from``

This extra attribute is used to map the editor's document state back to the dialog form field's
value. It is applied whenever the user opens the dialog form for an existing mark or node element in
the editor. This attribute can take three types of values:

* **A key value**: This is used to map the editor's document state using a key and map it to the
  given field' value of the dialog form.
* **A functional expression**: This is used to map the editor's document state using a JavaScript
  lambda function. This snippet has access to all attributes of the editor's document state and
  must return one or more `properties or attributes`_ of the dialog form's field. If the field is an
  HTMLInputElement_ or HTMLSelectElement_, then this lamda function usually returns an object
  containing ``{value: …}``. The editor's document state can be accessed using ``attributes.…``
  inside this snippet.

  Example: ``{dataset: {fileupload: JSON.stringify(attributes.dataset)}}`` maps the value of the
  attribute ``dataset`` of the editor's document state to the ``dataset`` attribute of the
  associated input field in the form dialog. 
* **The name of a function followed by brackets**, for instance ``change_link_type()``. This
  function must be an attribute of the object declared inside the extension script as explained in
  the previous section. As its first argument it takes the field of the dialog form, usually an
  HTMLInputElement_ or HTMLSelectElement_. As its second argument it receives the editor's document
  state for the given mark or node as a plain JavaScript object. This function then shall modify the
  given input element's ``value`` or ``checked`` property, or any of its attributes.

  Example: Say, that in our ``CustomHyperlinkDialogForm`` we perfer a ``RadioSelect`` widget to
  select the link type. Now the problem is, that we have one radio input element for each choice.
  Inside our extension script we can therefore implement this mapping function:

  .. code-block:: javascript
	:caption: myapp/tiptap-extensions/custom_hyperlink.js

	{
	    ...
	
	    change_link_type(inputElement, attributes) {
	        if (attributes.page && inputElement.value === "internal") {
	           inputElement.checked = true;
	        } else if (attributes.href && inputElement.value === "external") {
	           inputElement.checked = true;
	        } else {
	           inputElement.checked = false;
	        }
	    },
	
	    ...
	}

  When opening the dialog, this function is called for each input element of its form. Since we
  don't have a single field we can map our editor's document state value to, we must lookup the
  named radio input element (actually we use ``value`` for this) and set its ``checked`` property
  accordingly. This way we can ensure that the correct radio input element is selected when opening
  the dialog form.

  The widget for our choice field ``link_type`` then must be rewritten to:
  
  .. code-block:: python

	class CustomHyperlinkDialogForm(dialogs.RichtextDialogForm):
	    ...
	    link_type = fields.ChoiceField(
	        ...
	        widget=RadioSelect(attrs={'richtext-map-from': 'change_link_type()'}),
	    )

.. _HTMLInputElement: https://developer.mozilla.org/en-US/docs/Web/API/HTMLInputElement
.. _HTMLSelectElement: https://developer.mozilla.org/en-US/docs/Web/API/HTMLSelectElement
.. _properties or attributes: https://arunrajeevan.medium.com/difference-between-attribute-and-property-in-html-world-70de9b7fb25c

.. note:: Dialog forms usually contain multiple fields, therefore the rule defined in the
	``richtext-map-from`` attribute is applied for each field of that form. Keep this in mind,
	especially when	using a ``RadioSelect`` or ``CheckboxSelectMultiple`` widget, because there
	you must modify the ``checked`` instead of the ``value`` property of the given input fields.


.. rubric:: ``richtext-bidirectional``

A common use-case is to map the value of a dialog form field to the editor's document state and vice
versa. This can be done by using the attributes ``richtext-map-to="fieldname"`` and
``richtext-map-from="fieldname"``, where *fieldname* is the name of the given dialog field. A
shortcut for avoiding this verbose syntax is to use the attribute ``richtext-bidirectional=True``.
This then maps the value of the dialog form field to the editor's state using the field's name as
the key. It also maps the value of the editor's document state back to the dialog form field using
the same key. Using this attribute is only allowed if neither ``richtext-map-to`` nor
``richtext-map-from`` are set on the dialog's field.


.. rubric:: ``richtext-selection``

This extra attribute is used to map the editor's selected text to the dialog form field's value. It
is applied whenever the user selects some text and wants to convert it into a mark or node element.
A ggod example is the hyperlink editor, where the user selects some text and clicks on the link
button. This attribute is used to set the initial value of the dialog form field to the selected
text.


.. hint:: **In order to better understand these mappings, try the Richtext editor above:**

	Enter some text, select a part of it and click on the link icon. A dialog form will open where
	you can set a link type and the URL. Click on "Apply" and the link will be set. Submit the form
	and examine the submitted POST data. You will see a "mark" with type ``custom_hyperlink``.
	This mark element then contains the attributes ``href`` and ``page_id``. The value of the
	``href`` attribute is the URL you have entered, the value of the ``page_id`` attribute is the
	primary key of the selected page. Depending on the link type you have selected, one of these
	attributes is set, the other one is empty. The link type itself is not stored in the document's
	payload.


Rendering the content
---------------------

The internal representation of the editor is a state object containing nodes and marks. To render
the content of the editor, we can use the ``render_richtext`` template tag as explained in
:ref:`rendering-richtext`.

For each custom extension, we must define their own rendering template. It must be named as the
extension itself adding the suffix ``.html``. The template must be placed in the project's folder
``templates/richtext`` for nodes, or in ``templates/richtext/marks`` for marks. If the extension may
contain children, the template must be able to render them recursively. Check the samples in folder
``formset/templates/richtext`` for various nodes and marks.

For our custom hyperlink extension, the template could look like this:

.. code-block:: django
	:caption: templates/richtext/marks/custom_hyperlink.html

	{% load page_url from hyperlink %}
	<a href="{% if attrs.page_id %}{% page_url attrs.page_id %}{% else %}{{ attrs.href }}{% endif %}">{{ text }}</a>

This template then is used by the richtext renderer and loaded whenever an element of type
``custom_hyperlink`` is encountered.
