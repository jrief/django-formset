from django.views.generic import TemplateView
from django.template.loader import render_to_string


class TiptapView(TemplateView):
    template_name = 'testapp/tiptap.html'


def test_render_heading():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'heading',
                'attrs': {
                    'level': 1
                },
                'content': [{
                    'type': 'text',
                    'text': 'The Title'
                }]
            }, {
                'type': 'paragraph'
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<h1>The Title</h1>'


def test_render_bold():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'This is '
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'bold'
                    }],
                    'text': 'bold'
                }, {
                    'type': 'text',
                    'text': ' text'
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<p>This is <strong>bold</strong> text</p>'


def test_render_italic():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'This is '
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'italic'
                    }],
                    'text': 'italic'
                }, {
                    'type': 'text',
                    'text': ' text'
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<p>This is <em>italic</em> text</p>'


def test_render_underline():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'This is '
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'underline'
                    }],
                    'text': 'underlined'
                }, {
                    'type': 'text',
                    'text': ' text'
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<p>This is <u>underlined</u> text</p>'


def test_render_bulletlist():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'bulletList',
                'content': [{
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 1'
                        }]
                    }]
                }, {
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 2'
                        }]
                    }]
                }, {
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 3'
                        }]
                    }]
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<ul><li><p>Item 1</p></li><li><p>Item 2</p></li><li><p>Item 3</p></li></ul>'


def test_render_orderedlist():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'orderedList',
                'content': [{
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 1'
                        }]
                    }]
                }, {
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 2'
                        }]
                    }]
                }, {
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 3'
                        }]
                    }]
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<ol><li><p>Item 1</p></li><li><p>Item 2</p></li><li><p>Item 3</p></li></ol>'


def test_render_horizontalrule():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'above'
                }]
            }, {
                'type': 'horizontalRule'
            }, {
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'below'
                }
            ]}
        ]}
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<p>above</p><hr><p>below</p>'


def test_render_link():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'Click '
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'link',
                        'attrs': {
                            'href': 'https://example.org',
                            'target': '_blank'
                        }
                    }],
                    'text': 'here'
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<p>Click <a href="https://example.org">here</a></p>'
