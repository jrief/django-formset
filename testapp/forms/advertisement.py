from django.forms import fields, forms, models, widgets

from formset.richtext import controls, dialogs
from formset.richtext.widgets import RichTextarea
from formset.widgets import Selectize

from testapp.models.page import PageModel

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
                "type": "custom_hyperlink",
                "attrs": {
                  "href": "http://example.org"
                }
              }
            ],
            "text": "Aquitani"
          },
          {
            "type": "text",
            "text": ", tertiam. "
          },
          {
            "type": "text",
            "marks": [
              {
                "type": "bold"
              }
            ],
            "text": "Contra legem facit qui id facit quod lex prohibet."
          },
          {
            "type": "text",
            "text": " Petierunt uti sibi concilium totius Galliae in diem certam indicere."
          }
        ]
      }
    ]
  }
}


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
            controls.Strike(),
            controls.Subscript(),
            controls.Superscript(),
            controls.Separator(),
            controls.ClearFormat(),
            controls.Redo(),
            controls.Undo(),
            controls.DialogControl(
                CustomHyperlinkDialogForm(),
                icon='formset/icons/link.svg',
            ),
            controls.DialogControl(dialogs.SimpleImageDialogForm()),
            controls.DialogControl(dialogs.PlaceholderDialogForm()),
            controls.DialogControl(dialogs.FootnoteDialogForm()),
        ],
        attrs={'placeholder': "Start typing …", 'use_json': True}),
        initial=initial_json['ad_text'],
        # initial=initial_html,
    )
