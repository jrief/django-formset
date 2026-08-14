from django.forms import fields, forms, models, widgets

from formset.richtext import controls, dialogs
from formset.widgets.richtext import RichTextarea

from testapp.forms.dialogs import CustomHyperlinkDialogForm, SpecialGeoMapDialogForm

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
                        "text": "Dear "
                    },
                    {
                        "type": "text",
                        "marks": [
                            {
                                "type": "procurator",
                                "attrs": {
                                    "variable_name": "first_name",
                                    "role": "placeholder"
                                }
                            }
                        ],
                        "text": "John"
                    },
                    {
                        "type": "text",
                        "text": ","
                    }
                ]
            },
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
                        "type": "simple_geomap",
                        "attrs": {
                            "content": {
                                "type": "FeatureCollection",
                                "bbox": [
                                    -8.554444313049318,
                                    41.103172309560755,
                                    -8.550356626510622,
                                    41.10559760505117
                                ],
                                "features": [
                                    {
                                        "type": "Feature",
                                        "properties": {
                                            "special_marker": {
                                                "body": {
                                                    "type": "doc",
                                                    "content": [
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
                                                                    "text": "Capela do Senhor do Palheirnho"
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
                                                                            "type": "italic"
                                                                        }
                                                                    ],
                                                                    "text": "Avintes"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            }
                                        },
                                        "geometry": {
                                            "type": "Point",
                                            "coordinates": [
                                                -8.552256,
                                                41.10432
                                            ]
                                        },
                                        "id": "default-marker:0"
                                    }
                                ]
                            }
                        }
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
    icon = 'testapp/icons/margin-bottom.svg'
    extension_type = 'node'


class AdvertisementForm(forms.Form):
    ad_text = fields.CharField(
        label="Advertisement Text",
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
                controls.DialogControl(CustomHyperlinkDialogForm()),
                controls.DialogControl(dialogs.SimpleImageDialogForm()),
                controls.DialogControl(dialogs.PlaceholderDialogForm()),
                controls.DialogControl(dialogs.FootnoteDialogForm()),
                controls.DialogControl(SpecialGeoMapDialogForm()),
            ]),
        ],
        attrs={'placeholder': "Start typing …", 'use_json': True, 'maxlength': 2000, 'style': 'height: 450px;'}),
        initial=initial_json['ad_text'],
    )
    extra_text = fields.CharField(
        label="Extra Text",
        widget=RichTextarea(
            control_elements=[
                controls.Bold(),
                controls.Italic(),
                controls.BulletList(),
                controls.OrderedList(),
                controls.DialogControl(CustomHyperlinkDialogForm()),
                controls.Separator(),
                controls.ClearFormat(),
                controls.Undo(),
                controls.Redo(),
            ],
            attrs={'maxlength': 500, 'style': 'height: 250px;'},
        )
    )
