.. _richtext-extensions:

===================
Richtext Extensions
===================

.. versionadded:: 1.4

Having a Richtext editor which can set simple property values such as **bold** or *italic* on
editable text elements is not a big deal, even the most basic implementation can do that. The
difficulty arises when you want to set more than one property on a certain element.

Take for instance the hyperlink, the most basic implementation requires two fields: the URL and the
text to display. But some implementers might want to set more properties, such as the rel_, the
target_ attribute or they want to use links to download files or to link onto phone numbers or email
addresses. If the Richtext editor shall be used in a CMS or an e-commerce site, one might want to
set a link to an internal CMS page or a product instead of an external URL. This requires a dialog
form to be shown, where the user can select a page or product and select this out of a list of
available options.

.. _rel: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a#rel
.. _target: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a#target

As we can see, there are many use cases where the implementer might want to extend the Richtext
editor with a custom dialog form adopted to his exact needs. Since **django-formset** provides a way
to declare :ref:`dialog-forms`, we can use this to adopt our hyperlink editor to accept any
arbitrary attribute value.

.. django-view:: pages_dialog

	from django.forms import fields, forms, models, widgets
	from formset.richtext import controls
	from formset.richtext import dialogs 
	from formset.richtext.widgets import RichTextarea
	from formset.widgets import Selectize
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
	        widget=widgets.URLInput(attrs={
	            'size': 50,
	            'richtext-map-to': '{href: elements.link_type.value == "external" ? elements.url.value : ""}',
	            'richtext-map-from': 'href',
	            'df-show': '.link_type == "external"',
	            'df-require': '.link_type == "external"',
	        }),
	    )
	    page = models.ModelChoiceField(
	        queryset=PageModel.objects.all(),
	        label="Internal Page",
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


.. rubric:: The ``text`` field

This field is the text to display inside the anchor element of the link. Since the selected text in
the editor is used as the link text, we have added the ``'richtext-selection': True`` attribute to
the input field. This attribute is used by the editor to set the selected text as the initial value
of the field and vice versa.


.. rubric:: The ``link_type`` field

This choice field is used to select the type of the link, which can either be an external link
specified by an URL, or an internal link specified by the primary key of an object of type
``PageModel``. The value of this field is not stored in the Richtext editor's document state,
therefore we use a functional snippets to map the document state's value to the dialog form's field:

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

We then can attach this dialog form to our ``RichTextarea`` widget by adding it to the list of
control elements.

.. django-view:: pages_form

	from django.forms import fields, forms

	class PagesForm(forms.Form):
	    text = fields.CharField(widget=RichTextarea(control_elements=[
	        controls.Bold(),
	        controls.Italic(),
	        controls.DialogControl(
	            CustomHyperlinkDialogForm(),
	            icon='formset/icons/link.svg',
	        ),
	    ]))

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


Behind the scenes
-----------------

The most tricky part of the implementation is the mapping of the form fields to the editor's
document state and vice versa. Dialog forms therefore need a way to bidirectionally exchange their
data with the Richtext editor. This is done by adding the extra attributes ``richtext-map-to`` and
``richtext-map-from`` to the form field widgets.


.. rubric:: ``richtext-map-to``

This extra attribute is used to map the value of the form field's value to the editor's document
state. It is applied whenever the user clicks on the "Apply" button of the dialog form. This
attribute can take three types of values:

* ``True``, which means that the field's value is mapped to the editor's document state using the
  field's name as the key. If set, it also is applied in the other direction, ``richtext-map-from``
  therefore is not required anymore.
* **A key value**. This is used to map the field's value to the editor's document state using the
  given key to map it onto another key. If a key value is used, one must also provide a
  ``richtext-map-from`` attribute. Read below for details.
* **A functional expression.** This is used to map the field's value to the editor's document state
  using a JavaScript lambda function. This snippet has access to all elements of the dialog form and
  can return a value to be mapped onto the editor's document state. Accessing the values of the
  elements can only be achieved using ``elements.…`` inside the snippet. This is the most flexible
  way, because it can take the values of other fields into account, transform them or perform extra
  logic.
  
  Example: ``{src: JSON.parse(elements.image.dataset.fileupload).download_url}`` maps the download
  URL of an uploaded image of an input element named ``image`` to the attribute ``src`` of the
  editor's document state implementing the mark extension ``<img src="…" />``.

.. rubric:: ``richtext-map-from``

This extra attribute is used to map the editor's document state back to the dialog form field's
value. It is applied whenever the user opens the dialog form for an existing mark or node element in
the editor. This attribute can take two types of values:

* A key value. This is used to map the editor's document state using a key and map it to the field
  of the dialog form with the given name.
* A functional expression. This is used to map the editor's document state using a JavaScript
  lambda function. This snippet has access to all attributes of the editor's document state and must
  return a value to be mapped onto the given field of the dialog form. Accessing the values of the
  attributes can only be achieved using ``attributes.…`` inside the snippet.

  Example: ``{dataset: {fileupload: JSON.stringify(attributes.dataset)}}`` maps the value of the
  attribute ``dataset`` of the editor's document state to the ``dataset`` attribute of the
  associated input field in the form dialog. 


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
