from django.forms import fields, forms, widgets

from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.renderers.bootstrap import FormRenderer as BootstrapFormRenderer
from formset.richtext import controls, dialogs
from formset.richtext.widgets import RichTextarea
from formset.widgets import Button, UploadedFileInput


initial_html = """
<p>
 Lorem ipsum dolor sit amet, <a href="http://example.org/">consectetur</a> adipisici elit, sed eiusmod tempor incidunt
 ut labore et dolore magna. <strong>Petierunt uti sibi concilium totius Galliae in diem certam indicere. </strong>
 <em>Excepteur sint obcaecat cupiditat non proident culpa. </em>
</p>
"""

initial_json = {
  "ad_text": {
    "type": "doc",
    "content": [
      {
        "type": "paragraph",
        "content": [
          {
            "type": "text",
            "text": "Morbi odio eros, volutpat ut pharetra vitae, lobortis sed nibh. Prima luce, cum quibus mons aliud consensu ab eo. Unam incolunt Belgae, aliam "
          },
          {
            "type": "text",
            "marks": [
              {
                "type": "link",
                "attrs": {
                  "href": "http://example.org",
                  "target": "_blank",
                  "rel": "noopener noreferrer nofollow",
                  "class": None
                }
              }
            ],
            "text": "Aquitani"
          },
          {
            "type": "text",
            "text": ", tertiam. Contra legem facit qui id facit quod lex prohibet. Petierunt uti sibi concilium totius Galliae in diem certam indicere."
          }
        ]
      }
    ]
  }
}


class LinkDialogForm(dialogs.RichtextDialogForm):
    title = "Edit Link"
    extension = 'link'
    plugin_type = 'mark'
    prefix = 'link_dialog'
    icon = 'formset/icons/link.svg'

    text = fields.CharField(
        label="Text",
        widget=widgets.TextInput(attrs={
            'richtext-selection': True,
            'size': 50,
        })
    )
    url = fields.URLField(
        label="Link",
        widget=widgets.URLInput(attrs={
            'size': 50,
            'richtext-mapping': 'href',
            'df-show': '.type == "external"',
        }),
    )
    type = fields.ChoiceField(
        label="Type",
        choices=[('internal', "Internal"), ('external', "External")],
        initial='external',
        widget=widgets.Select(attrs={'richtext-mapping': True}),
    )


class ImageDialogForm(dialogs.RichtextDialogForm):
    title = "Edit Image"
    extension = 'image'
    plugin_type = 'node'
    icon = 'formset/icons/image.svg'
    prefix = 'image_dialog'

    image = fields.ImageField(
        label="Image",
        widget=UploadedFileInput(attrs={
            'richtext-dataset': 'fileupload',
            'richtext-mapping': '{src: JSON.parse(element.dataset.fileupload).download_url}',
        }),
    )
    dismiss = Activator(
        label="Close",
        widget=Button(
            action='dismiss',
        ),
    )
    revert = Activator(
        label="Revert",
        widget=Button(
            action='revert',
            button_variant=ButtonVariant.DANGER,
        ),
    )
    apply = Activator(
        label="Apply",
        widget=Button(
            action='apply',
            button_variant=ButtonVariant.PRIMARY,
            attrs={'auto-disable': True},
        ),
    )


class AdvertisementForm(forms.Form):
    ad_text = fields.CharField(
        widget=RichTextarea(control_elements=[
            controls.Heading([1,2,3]),
            controls.Bold(),
            controls.Blockquote(),
            controls.CodeBlock(),
            controls.HardBreak(),
            controls.Italic(),
            controls.Underline(),
            #controls.TextColor(['rgb(212, 0, 0)', 'rgb(0, 212, 0)', 'rgb(0, 0, 212)']),
            controls.TextColor(['text-red', 'text-green', 'text-blue']),
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
            controls.DialogControl(dialogs.SimpleLinkDialogForm()),
            controls.DialogControl(dialogs.SimpleImageDialogForm()),
            controls.DialogControl(dialogs.PlaceholderDialogForm()),
        ],
        attrs={'placeholder': "Start typing …"}),
        initial=initial_html,
    )
