import pytest

from django.conf import settings
from django.core.management import call_command
from django.views.generic import TemplateView
from django.template.loader import render_to_string
from django.utils.html import strip_spaces_between_tags

from testapp.models import PageModel


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
                    'text': 'The Title',
                }]
            }, {
                'type': 'paragraph',
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
                    'text': 'This is ',
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'bold',
                    }],
                    'text': 'bold',
                }, {
                    'type': 'text',
                    'text': ' text',
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
                    'text': 'This is ',
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'italic',
                    }],
                    'text': 'italic',
                }, {
                    'type': 'text',
                    'text': ' text',
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
                    'text': 'This is ',
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'underline',
                    }],
                    'text': 'underlined'
                }, {
                    'type': 'text',
                    'text': ' text',
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
                            'text': 'Item 1',
                        }]
                    }]
                }, {
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 2',
                        }]
                    }]
                }, {
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 3',
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
                            'text': 'Item 1',
                        }]
                    }]
                }, {
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 2',
                        }]
                    }]
                }, {
                    'type': 'listItem',
                    'content': [{
                        'type': 'paragraph',
                        'content': [{
                            'type': 'text',
                            'text': 'Item 3',
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
                    'text': 'above',
                }]
            }, {
                'type': 'horizontalRule',
            }, {
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'below',
                }
            ]}
        ]}
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<p>above</p><hr><p>below</p>'


def test_render_simple_link():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'Click ',
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'simple_link',
                        'attrs': {
                            'href': 'https://example.org',
                            'target': '_blank',
                        }
                    }],
                    'text': 'here',
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<p>Click <a href="https://example.org">here</a></p>'


def test_render_placeholder():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'Dear '
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'procurator',
                        'attrs': {
                            'variable_name': 'full_name',
                            'sample_value': 'John Doe',
                            'role': 'placeholder',
                        },
                    }],
                    'text': 'John Doe',
                }, {
                    'type': 'text',
                    'text': ', you have been elected!',
                }],
            }],
        },
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == '<p>Dear {{ full_name|default:"John Doe" }}, you have been elected!</p>'


def test_render_footnote():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'Douglas Crockford specified the data format JSON'
                }, {
                    'type': "footnote",
                    'attrs': {
                        'content': {
                            'type': 'doc',
                            'content': [{
                                'type': 'paragraph',
                                'content': [{
                                    'type': 'text',
                                    'marks': [
                                         {'type': 'bold'},
                                    ],
                                    'text': 'JSON',
                                }, {
                                    'type': 'text',
                                    'text': ': ',
                                }, {
                                    'type': 'text',
                                    'marks': [{
                                        'type': 'simple_link',
                                        'attrs': {
                                            'href': 'https://en.wikipedia.org/wiki/JSON',
                                        }
                                    }],
                                    'text': 'JavaScript Object Notation',
                                }]
                            }]
                        },
                        'role': 'note',
                    }
                }, {
                    'type': 'text',
                    'text': '.',
                }],
            }],
        },
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == strip_spaces_between_tags('''
<p>Douglas Crockford specified the data format JSON<sup><a href="#_footnote-1">[1]</a></sup>.</p>
<ol>
    <li id="_footnote-1">
        <p><strong>JSON</strong>: <a href="https://en.wikipedia.org/wiki/JSON">JavaScript Object Notation</a></p>
    </li>
</ol>
''').replace('\t', '').replace('\n', '')


def test_render_alternative_template():
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'This is ',
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'bold',
                    }],
                    'text': 'bold',
                }, {
                    'type': 'text',
                    'text': ' ',
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'italic',
                    }],
                    'text': 'and italic',
                }, {
                    'type': 'text',
                    'text': ' text.',
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap-alternative.html', context)
    assert html == '<article><p>This is <strong>bold</strong><em>and italic</em> text.</p></article>'


@pytest.fixture(scope='function')
def django_db_setup(django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', settings.BASE_DIR / 'testapp/fixtures/pages.json', verbosity=0)


@pytest.mark.django_db
def test_render_custom_hyperlink():
    page = PageModel.objects.order_by('?').first()
    context = {'object': {
        'text': {
            'type': 'doc',
            'content': [{
                'type': 'paragraph',
                'content': [{
                    'type': 'text',
                    'text': 'Click on this ',
                }, {
                    'type': 'text',
                    'marks': [{
                        'type': 'custom_hyperlink',
                        'attrs': {
                            'page_id': page.id,
                        }
                    }],
                    'text': 'page',
                }]
            }]
        }
    }}
    html = render_to_string('testapp/tiptap.html', context)
    assert html == f'<p>Click on this <a href="{page.get_absolute_url()}">page</a></p>'
