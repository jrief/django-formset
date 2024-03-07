from django.forms import fields, forms, widgets

from formset.dialog import DialogForm
from formset.fields import Activator
from formset.renderers import ButtonVariant
from formset.renderers.bootstrap import FormRenderer as BootstrapFormRenderer
from formset.richtext import controls
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


class LinkDialogForm(DialogForm):
    title = "Edit Link"
    is_transient = True
    extension = 'link'
    prefix = 'link_dialog'
    induce_close = 'dismiss:active || revert:active || apply:active'

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
        ),
    )


class ImageDialogForm(DialogForm):
    title = "Edit Image"
    is_transient = True
    extension = 'image'
    prefix = 'image_dialog'
    induce_close = 'dismiss:active || revert:active || apply:active'

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


class PlaceholderDialogForm(DialogForm):
    title = "Edit Placeholder"
    is_transient = True
    extension = 'procurator'
    prefix = 'placeholder_dialog'
    induce_close = 'dismiss:active || revert:active || apply:active'

    variable_name = fields.RegexField(
        regex=r'^[A-Za-z_][0-9A-Za-z_\.]{0,254}$',
        label="Variable Name",
        widget=widgets.TextInput(attrs={
            'richtext-mapping': True,
            'size': 50,
            'pattern': '[A-Za-z_][0-9A-Za-z_\.]{0,254}',
        }),
    )
    sample_value = fields.CharField(
        label="Sample Value",
        widget=widgets.TextInput(attrs={
            'richtext-selection': True,
            'size': 50,
        })
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
            controls.DialogAction(name='dialog_link', dialog_form=LinkDialogForm(renderer=BootstrapFormRenderer()), icon='formset/icons/link.svg'),
            controls.DialogAction(name='dialog_image', dialog_form=ImageDialogForm(renderer=BootstrapFormRenderer()), icon='formset/icons/image.svg'),
            controls.DialogAction(name='dialog_procurator', dialog_form=PlaceholderDialogForm(renderer=BootstrapFormRenderer()), icon='formset/icons/placeholder.svg'),
        ],
        attrs={'placeholder': "Start typing …"}),
        initial=initial_html,
    )
