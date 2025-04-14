from django.forms import fields, forms, models, widgets

from formset.richtext import controls, dialogs
from formset.widgets import RichTextarea
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
                                    "href": "http://example.org",
                                }
                            }
                        ],
                        "text": "Aquitani"
                    },
                    {
                        "type": "text",
                        "text": ", tertiam."
                    },
                    {
                        "type": "footnote",
                        "attrs": {
                            "content": {
                                "type": "doc",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [
                                            {
                                                "type": "text",
                                                "marks": [
                                                    {
                                                        "type": "italic"
                                                    }
                                                ],
                                                "text": "Belgae "
                                            },
                                            {
                                                "type": "text",
                                                "marks": [
                                                    {
                                                        "type": "simple_link",
                                                        "attrs": {
                                                            "href": "http://example.org"
                                                        }
                                                    },
                                                    {
                                                        "type": "italic"
                                                    }
                                                ],
                                                "text": "Aquitani"
                                            },
                                            {
                                                "type": "text",
                                                "marks": [
                                                    {
                                                        "type": "italic"
                                                    }
                                                ],
                                                "text": ", tertiam."
                                            }
                                        ]
                                    },
                                    {
                                        "type": "paragraph"
                                    }
                                ]
                            },
                            "role": "note"
                        }
                    }
                ]
            },
            {
                "type": "paragraph",
                "content": [
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


font_family_classes = {
    'open-sans-regular': "Open Sans",
    'dancing-script-regular': "Dancing Script",
    'lato-regular': "Lato",
    'merriweather-regular': "Merriweather",
    'montserrat-regular': "Montserrat",
    'roboto-regular': "Roboto",
    'pacifio-regular': "Pacifico",
    'incosolata-regular': "Incosolata",
    'playfair-display-regular': "Playfair Display",
}


font_size_classes = {
    'font-size-small': "Small",
    'font-size-smaller': "Smaller",
    'font-size-large': "Large",
    'font-size-larger': "Larger",
}


line_height_classes = {
    'line-height-small': "Small",
    'line-height-medium': "Medium",
    'line-height-double': "Double",
}


margin_bottom_classes = {
    'margin-bottom-1': "Small",
    'margin-bottom-2': "Medium",
    'margin-bottom-3': "Double",
}


class MarginBottom(controls.ClassBaseControlElement):
    extension = 'marginBottom'
    label = "Margin Bottom"
    icon = 'testapp/margin-bottom.svg'
    extension_type = 'node'


class AdvertisementForm(forms.Form):
    ad_text = fields.CharField(
        widget=RichTextarea(control_elements=[
            controls.Group([
                controls.Heading([1,2,3]),
                controls.Bold(),
                controls.Blockquote(),
                controls.CodeBlock(),
                controls.HardBreak(),
                controls.Italic(),
                controls.Underline(),
            ]),
            controls.Group([
                controls.TextColor(['text-red', 'text-green', 'text-blue']),
                #controls.TextColor(['rgb(212, 0, 0)', 'rgb(0, 212, 0)', 'rgb(0, 0, 212)']),
                controls.FontFamily(font_family_classes),
                controls.FontSize(font_size_classes),
                controls.LineHeight(line_height_classes),
                MarginBottom(margin_bottom_classes),
                controls.Separator(),
                controls.TextIndent(),
                controls.TextIndent('outdent'),
                controls.TextMargin('increase'),
                controls.TextMargin('decrease'),
                controls.TextAlign(['left', 'center', 'right']),
            ]),
            controls.Group([
                controls.HorizontalRule(),
                controls.Strike(),
                controls.Subscript(),
                controls.Superscript(),
            ]),
            controls.Group([
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
            ]),
        ],
        attrs={'placeholder': "Start typing …", 'use_json': True, 'maxlength': 2000}),
        initial=initial_json['ad_text'],
    )
