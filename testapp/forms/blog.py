from django.forms import fields, models, widgets

from formset.formfields.richtext import RichTextField
from formset.richtext import controls, dialogs
from formset.widgets import UploadedFileInput
from formset.widgets.richtext import RichTextarea

from testapp.models.blog import BlogModel


class CustomImageDialogForm(dialogs.RichtextDialogForm):
    title = "Edit Image"
    extension = 'custom_image'
    extension_script = 'testapp/tiptap-extensions/custom_image.js'
    icon = 'formset/richtext/icons/image.svg'
    plugin_type = 'node'
    prefix = 'custom_image_dialog'

    image = fields.ImageField(
        label="Uploaded Image",
        widget=UploadedFileInput(attrs={
            'richtext-map-to': '{src: JSON.parse(elements.image.dataset.fileupload).download_url, height: elements.height.value, dataset: JSON.parse(elements.image.dataset.fileupload)}',
            'richtext-map-from': '{dataset: {fileupload: JSON.stringify(attributes.dataset)}}',
        }),
    )
    height = fields.IntegerField(
        label="Image Height",
        widget=widgets.NumberInput(attrs={
            'richtext-map-from': '{value: attributes.height}',
        }),
        min_value=40,
        max_value=1000,
    )


class BlogModelForm(models.ModelForm):
    body = RichTextField(
        label="Personal Blog",
        upload_to='blog_images',
        widget=RichTextarea(
            control_elements=[
                controls.Heading([1, 2, 3]),
                controls.Bold(),
                controls.Blockquote(),
                controls.CodeBlock(),
                controls.HardBreak(),
                controls.Italic(),
                controls.Underline(),
                controls.BulletList(),
                controls.OrderedList(),
                controls.TextColor(['rgb(212, 0, 0)', 'rgb(0, 212, 0)', 'rgb(0, 0, 212)']),
                # controls.TextColor(['text-red', 'text-green', 'text-blue']),
                controls.DialogControl(CustomImageDialogForm()),
                controls.TextIndent(),
                controls.TextIndent('outdent'),
                controls.TextMargin('increase'),
                controls.TextMargin('decrease'),
                controls.TextAlign(['left', 'center', 'right']),
                controls.HorizontalRule(),
                controls.Subscript(),
                controls.Superscript(),
                controls.Separator(),
                controls.ClearFormat(),
                controls.Redo(),
                controls.Undo(),
            ],
            attrs={'placeholder': "Start typing …"},
        ),
    )

    class Meta:
        model = BlogModel
        fields = '__all__'
