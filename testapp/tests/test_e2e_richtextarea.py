from time import sleep

import pytest
from playwright.sync_api import expect

from django.forms import fields, forms
from django.urls import path

from formset.richtext import controls, dialogs
from formset.widgets import RichTextarea
from formset.views import FormView

from .utils import ContextMixin, get_javascript_catalog


font_family_classes = {
    'font-family-a': "Font A",
    'font-family-b': "Font B",
    'font-family-c': "Font C",
}


font_size_classes = {
    'font-size-small': "Small",
    'font-size-medium': "Medium",
    'font-size-large': "Large",
}


line_height_classes = {
    'line-height-small': "Small",
    'line-height-medium': "Medium",
    'line-height-large': "Large",
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


control_elements = [
    controls.Heading([1, 2, 3]),
    controls.Bold(),
    controls.Italic(),
    controls.Underline(),
    controls.Blockquote(),
    controls.FontFamily(font_family_classes),
    controls.FontSize(font_size_classes),
    controls.LineHeight(line_height_classes),
    MarginBottom(margin_bottom_classes),
    controls.HorizontalRule(),
    controls.DialogControl(dialogs.SimpleLinkDialogForm()),
    controls.DialogControl(dialogs.FootnoteDialogForm()),
    controls.Separator(),
    controls.Redo(),
    controls.Undo(),
]


control_elements_mini = [
    controls.Heading(2),
    controls.Bold(),
    controls.Italic(),
    controls.Underline(),
    controls.Separator(),
    controls.Redo(),
    controls.Undo(),
]


class PlainRichTextForm(forms.Form):
    text = fields.CharField(
        widget=RichTextarea(control_elements=control_elements),
    )


class PlainRichTextMiniForm(forms.Form):
    text = fields.CharField(
        widget=RichTextarea(control_elements=control_elements_mini),
    )


class JSONRichTextForm(forms.Form):
    text = fields.JSONField(
        widget=RichTextarea(control_elements=control_elements),
    )


class DemoFormView(ContextMixin, FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('plain_richtext', DemoFormView.as_view(
        form_class=PlainRichTextForm,
    ), name='plain_richtext'),
    path('plain_richtext_mini', DemoFormView.as_view(
        form_class=PlainRichTextMiniForm,
    ), name='plain_richtext_mini'),
    path('plain_richtext_initialized', DemoFormView.as_view(
        form_class=PlainRichTextForm,
        initial={'text': '<p>Click <a href="https://example.org/">here</a></p>'},
    ), name='plain_richtext_initialized'),
    path('json_richtext', DemoFormView.as_view(
        form_class=JSONRichTextForm,
    ), name='json_richtext'),
    get_javascript_catalog(),
]


@pytest.fixture
def richtext_wrapper(page):
    wrapper = page.locator('.dj-richtext-wrapper').first
    expect(wrapper).to_be_visible()
    return wrapper


@pytest.fixture
def menubar(richtext_wrapper):
    menubar = richtext_wrapper.locator('[role="menubar"]').first
    expect(menubar).to_be_visible()
    return menubar


@pytest.fixture
def contenteditable(richtext_wrapper):
    contenteditable = richtext_wrapper.locator('[contenteditable="true"]').last
    expect(contenteditable).to_be_visible()
    return contenteditable


def select_text(paragraph, start, end):
    paragraph.evaluate(f'''paragraph => {{
        const selection = window.getSelection();
        const range = document.createRange();
        let start = {start};
        for (let k = 0; k < paragraph.childNodes.length; k++) {{
            let childNode = paragraph.childNodes[k];
            if (childNode instanceof HTMLSpanElement) {{
                if (start > childNode.innerText.length) {{
                    start -= childNode.innerText.length;
                }} else {{
                    childNode = childNode.childNodes[0];
                }}
            }}
            if (childNode instanceof Text) {{
                if (start > childNode.length) {{
                    start -= childNode.length;
                }} else {{
                    range.setStart(childNode, start);
                    break;
                }}
            }}
        }}
        let end = {end};
        for (let k = 0; k < paragraph.childNodes.length; k++) {{
            let childNode = paragraph.childNodes[k];
            if (childNode instanceof HTMLSpanElement) {{
                if (end > childNode.innerText.length) {{
                    end -= childNode.innerText.length;
                }} else {{
                    childNode = childNode.childNodes[0];
                }}
            }}
            if (childNode instanceof Text) {{
                if (end > childNode.length) {{
                    end -= childNode.length;
                }} else {{
                    range.setEnd(childNode, end);
                    break;
                }}
            }}
        }}
        selection.removeAllRanges();
        selection.addRange(range);
    }}''')


def set_caret(page, contenteditable, position):
    contenteditable.click(position={'x': 2, 'y': 2})
    page.keyboard.press('Home')
    sleep(0.05)
    for _ in range(position):
        page.keyboard.press('ArrowRight')
        sleep(0.05)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
@pytest.mark.parametrize('control', [('bold', 'strong'), ('italic', 'em'), ('underline', 'u')])
def test_tiptap_marks(page, viewname, menubar, contenteditable, control):
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    contenteditable.type(lorem)
    assert contenteditable.inner_html() == f"<p>{lorem}</p>"
    select_text(contenteditable.locator('p'), 6, 11)
    button = menubar.locator(f'[richtext-click="{control[0]}"]')
    button.click()
    assert contenteditable.inner_html() == f"<p>{lorem[:6]}<{control[1]}>{lorem[6:11]}</{control[1]}>{lorem[11:]}</p>"
    set_caret(page, contenteditable, 9)
    expect(button).to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_many_headings(page, viewname, menubar, contenteditable):
    heading = "Tiptap Editor"
    contenteditable.type(heading)
    assert contenteditable.inner_html() == f"<p>{heading}</p>"
    set_caret(page, contenteditable, 0)
    menu_button = menubar.locator('[richtext-click="heading"]')
    submenu = menubar.locator('[richtext-click="heading"] + ul[role="menu"]')
    expect(submenu).not_to_be_visible()
    menu_button.click()
    expect(submenu).to_be_visible()
    submenu.locator('[richtext-click="heading:1"]').click()
    assert contenteditable.inner_html() == f"<h1>{heading}</h1>"
    set_caret(page, contenteditable, 5)
    expect(menu_button).to_have_class('active')
    expect(submenu).not_to_be_visible()
    menu_button.click()
    expect(submenu).to_be_visible()
    expect(submenu.locator('li:first-child')).to_have_class('active')
    expect(submenu.locator('li:nth-child(2)')).not_to_have_class('active')
    expect(submenu.locator('li:nth-child(3)')).not_to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext_mini'])
def test_tiptap_single_heading(page, viewname, menubar, contenteditable):
    heading = "Tiptap Editor"
    contenteditable.type(heading)
    assert contenteditable.inner_html() == f"<p>{heading}</p>"
    set_caret(page, contenteditable, 0)
    menu_button = menubar.locator('[richtext-click="heading:2"]')
    submenu = menubar.locator('[richtext-click="heading:2"] + ul[role="menu"]')
    expect(submenu).to_have_count(0)  # no submenu for single heading
    menu_button.click()
    assert contenteditable.inner_html() == f"<h2>{heading}</h2>"
    set_caret(page, contenteditable, 5)
    expect(menu_button).to_have_class('active')
    menu_button.click()  # toggle has no affect
    assert contenteditable.inner_html() == f"<h2>{heading}</h2>"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_blockquote(page, viewname, menubar, contenteditable):
    block = "Tiptap Block"
    contenteditable.type(block)
    assert contenteditable.inner_html() == f"<p>{block}</p>"
    set_caret(page, contenteditable, 0)
    menu_button = menubar.locator('[richtext-click="blockquote"]')
    menu_button.click()
    assert contenteditable.inner_html() == f"<blockquote><p>{block}</p></blockquote>"
    set_caret(page, contenteditable, 5)
    expect(menu_button).to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_classbased_mark(page, viewname, menubar, contenteditable):
    lorem = "Lorem ipsum dolor sit amet."
    contenteditable.type(lorem)
    assert contenteditable.inner_html() == f"<p>{lorem}</p>"
    select_text(contenteditable.locator('p'), 6, 17)
    family_menu_button = menubar.locator('[richtext-click="classBasedMark:fontFamily"]')
    family_menu_button.click()
    expect(family_menu_button.locator('+ ul[role="menu"]')).to_be_visible()
    submenu_items = family_menu_button.locator('+ ul[role="menu"] > li')
    expect(submenu_items).to_have_count(4)
    submenu_items.nth(2).click()
    assert contenteditable.inner_html() == '<p>Lorem <span class="font-family-b">ipsum dolor</span> sit amet.</p>'
    set_caret(page, contenteditable, 8)
    expect(family_menu_button).to_have_class('active')
    expect(submenu_items.nth(2)).to_have_class('active')
    set_caret(page, contenteditable, 18)
    expect(family_menu_button).not_to_have_class('active')
    family_menu_button.click()
    for item in submenu_items.all():
        expect(item).not_to_have_class('active')

    # add another class to overlapping selection
    select_text(contenteditable.locator('p'), 11, 21)
    size_menu_button = menubar.locator('[richtext-click="classBasedMark:fontSize"]')
    size_menu_button.click()
    submenu_items = size_menu_button.locator('+ ul[role="menu"] > li')
    expect(submenu_items).to_have_count(4)
    submenu_items.nth(2).click()
    assert contenteditable.inner_html() == '<p>Lorem <span class="font-family-b">ipsum<span class="font-size-medium"> dolor</span></span><span class="font-size-medium"> sit</span> amet.</p>'
    set_caret(page, contenteditable, 8)
    expect(family_menu_button).to_have_class('active')
    expect(size_menu_button).not_to_have_class('active')
    set_caret(page, contenteditable, 18)
    expect(family_menu_button).not_to_have_class('active')
    expect(size_menu_button).to_have_class('active')
    set_caret(page, contenteditable, 3)
    expect(family_menu_button).not_to_have_class('active')
    expect(size_menu_button).not_to_have_class('active')
    size_menu_button.click()
    for item in submenu_items.all():
        expect(item).not_to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_classbased_node(page, viewname, menubar, contenteditable):
    lorem = "Lorem ipsum dolor sit amet."
    contenteditable.type(lorem)
    assert contenteditable.inner_html() == f"<p>{lorem}</p>"
    set_caret(page, contenteditable, 1)
    lineheight_menu_button = menubar.locator('[richtext-click="classBasedNode:lineHeight"]')
    lineheight_menu_button.click()
    expect(lineheight_menu_button.locator('+ ul[role="menu"]')).to_be_visible()
    submenu_items = lineheight_menu_button.locator('+ ul[role="menu"] > li')
    expect(submenu_items).to_have_count(4)
    submenu_items.nth(2).click()
    assert contenteditable.inner_html() == '<p class="line-height-medium">Lorem ipsum dolor sit amet.</p>'
    expect(lineheight_menu_button).to_have_class('active')
    expect(lineheight_menu_button.locator('+ ul[role="menu"] > li').nth(2)).to_have_class('active')
    marginbottom_menu_button = menubar.locator('[richtext-click="classBasedNode:marginBottom"]')
    marginbottom_menu_button.click()
    expect(marginbottom_menu_button.locator('+ ul[role="menu"]')).to_be_visible()
    submenu_items = marginbottom_menu_button.locator('+ ul[role="menu"] > li')
    expect(submenu_items).to_have_count(4)
    submenu_items.nth(2).click()
    assert contenteditable.inner_html() == '<p class="line-height-medium margin-bottom-2">Lorem ipsum dolor sit amet.</p>'
    set_caret(page, contenteditable, 1)
    expect(lineheight_menu_button).to_have_class('active')
    expect(marginbottom_menu_button).to_have_class('active')
    expect(marginbottom_menu_button.locator('+ ul[role="menu"] > li').nth(2)).to_have_class('active')
    lineheight_menu_button.click()
    submenu_items = lineheight_menu_button.locator('+ ul[role="menu"] > li')
    submenu_items.nth(0).click()
    set_caret(page, contenteditable, 1)
    expect(lineheight_menu_button).not_to_have_class('active')
    expect(marginbottom_menu_button).to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_valid_simple_link(page, viewname, richtext_wrapper, menubar, contenteditable):
    clickme = "Click here"
    contenteditable.type(clickme)
    assert contenteditable.inner_html() == f"<p>{clickme}</p>"
    select_text(contenteditable.locator('p'), 6, 10)
    menu_button = menubar.locator('button[name="dialog_simple_link"]')
    dialog = richtext_wrapper.locator('dialog[df-induce-open="dialog_simple_link:active"]').first
    expect(dialog).not_to_be_visible()
    menu_button.click()
    expect(dialog).to_be_visible()
    text_input = dialog.locator('input[name="text"]')
    expect(text_input).to_have_value("here")
    link_input = dialog.locator('input[name="url"]')
    expect(link_input).to_have_value("")
    link_input.type("https://example.org/")
    expect(link_input).to_have_value("https://example.org/")
    expect(dialog.locator('button[name="revert"]')).not_to_be_visible()
    dialog.locator('button[name="apply"]').click()
    expect(dialog).not_to_be_visible()
    expect(contenteditable.locator('p')).to_have_text('Click here')
    expect(contenteditable.locator('p a')).to_have_text('here')
    expect(contenteditable.locator('p a')).to_have_attribute('href', 'https://example.org/')
    set_caret(page, contenteditable, 9)
    expect(menu_button).to_have_class('active')
    set_caret(page, contenteditable, 2)
    expect(menu_button).not_to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_invalid_simple_link(page, viewname, richtext_wrapper, menubar, contenteditable):
    clickme = "Click here"
    contenteditable.type(clickme)
    assert contenteditable.inner_html() == f"<p>{clickme}</p>"
    select_text(contenteditable.locator('p'), 6, 10)
    menu_button = menubar.locator('button[name="dialog_simple_link"]')
    dialog = richtext_wrapper.locator('dialog[df-induce-open="dialog_simple_link:active"]').first
    expect(dialog).not_to_be_visible()
    menu_button.click()
    expect(dialog).to_be_visible()
    text_input = dialog.locator('input[name="text"]')
    expect(text_input).to_have_value("here")
    link_input = dialog.locator('input[name="url"]')
    expect(link_input).to_have_value("")
    link_input.type("www.example.org")
    dialog.click(position={'x': 1, 'y': 1})
    placeholder = dialog.locator('input[name="url"] + .dj-field-errors .dj-placeholder')
    expect(placeholder).to_have_text("Enter a valid URL.")
    dialog.locator('button[name="apply"]').click()
    expect(dialog).to_be_visible()
    dialog.locator('button[name="cancel"]').click()
    expect(dialog).not_to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext_initialized'])
def test_tiptap_remove_simple_link(page, viewname, menubar, contenteditable):
    assert contenteditable.inner_html() == '<p>Click <a href="https://example.org/">here</a></p>'
    dialog = page.locator('dialog[df-induce-open="dialog_simple_link:active"]').first
    expect(dialog).not_to_be_visible()
    link_element = contenteditable.locator('p > a[href]')
    expect(link_element).to_have_text("here")
    link_element.click(); sleep(0.02); link_element.click()  # dblclick() does not work here
    expect(dialog).to_be_visible()
    text_input = dialog.locator('input[name="text"]')
    expect(text_input).to_have_value("here")
    link_input = dialog.locator('input[name="url"]')
    expect(link_input).to_have_value("https://example.org/")
    dialog.locator('button[name="revert"]').click()
    expect(dialog).not_to_be_visible()
    assert contenteditable.inner_html() == '<p>Click here</p>'
