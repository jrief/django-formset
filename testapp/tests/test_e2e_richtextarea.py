from time import sleep

import pytest
from playwright.sync_api import expect

from django.forms import fields, forms
from django.urls import path

from formset.richtext import controls, dialogs
from formset.widgets.richtext import RichTextarea
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


def select_text(page, paragraph, start, end):
    paragraph.evaluate(f'''paragraph => {{
        const selection = window.getSelection();
        const range = document.createRange();
        const walker = document.createTreeWalker(paragraph, NodeFilter.SHOW_TEXT);
        let start = {start};
        while (walker.nextNode()) {{
            const node = walker.currentNode;
            if (start <= node.length) {{
                range.setStart(node, start);
                break;
            }}
            start -= node.length;
        }}
        let end = {end};
        walker.currentNode = paragraph;
        while (walker.nextNode()) {{
            const node = walker.currentNode;
            if (end <= node.length) {{
                range.setEnd(node, end);
                break;
            }}
            end -= node.length;
        }}
        selection.removeAllRanges();
        selection.addRange(range);
        document.dispatchEvent(new Event('selectionchange'));
    }}''')
    wait_until_idle(page)


def wait_until_idle(page):
    page.evaluate('() => new Promise(resolve => requestIdleCallback(resolve))')


def set_caret(page, contenteditable, position):
    contenteditable.evaluate(f'''contenteditable => {{
        contenteditable.focus();
        const walker = document.createTreeWalker(contenteditable, NodeFilter.SHOW_TEXT);
        let pos = {position};
        while (walker.nextNode()) {{
            const node = walker.currentNode;
            if (pos <= node.length) {{
                const selection = window.getSelection();
                const range = document.createRange();
                range.setStart(node, pos);
                range.collapse(true);
                selection.removeAllRanges();
                selection.addRange(range);
                document.dispatchEvent(new Event('selectionchange'));
                return;
            }}
            pos -= node.length;
        }}
    }}''')
    wait_until_idle(page)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
@pytest.mark.parametrize('control', [('bold', 'strong'), ('italic', 'em'), ('underline', 'u')])
def test_tiptap_marks(page, viewname, menubar, contenteditable, control):
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    contenteditable.type(lorem)
    expect(contenteditable.locator('p')).to_have_text(lorem)
    select_text(page, contenteditable.locator('p'), 6, 11)
    button = menubar.locator(f'[richtext-click="{control[0]}"]')
    button.click()
    wait_until_idle(page)
    expect(contenteditable.locator(f'p > {control[1]}')).to_have_text(lorem[6:11])
    set_caret(page, contenteditable, 9)
    expect(button).to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_many_headings(page, viewname, menubar, contenteditable):
    heading = "Tiptap Editor"
    contenteditable.type(heading)
    expect(contenteditable.locator('p')).to_have_text(heading)
    set_caret(page, contenteditable, 0)
    menu_button = menubar.locator('[richtext-click="heading"]')
    submenu = menubar.locator('[richtext-click="heading"] + ul[role="menu"]')
    expect(submenu).not_to_be_visible()
    menu_button.click()
    expect(submenu).to_be_visible()
    submenu.locator('[richtext-click="heading:1"]').click()
    expect(contenteditable.locator('h1')).to_have_text(heading)
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
    expect(contenteditable.locator('p')).to_have_text(heading)
    set_caret(page, contenteditable, 0)
    menu_button = menubar.locator('[richtext-click="heading:2"]')
    submenu = menubar.locator('[richtext-click="heading:2"] + ul[role="menu"]')
    expect(submenu).to_have_count(0)  # no submenu for single heading
    menu_button.click()
    expect(contenteditable.locator('h2')).to_have_text(heading)
    set_caret(page, contenteditable, 5)
    expect(menu_button).to_have_class('active')
    menu_button.click()  # toggle has no affect
    expect(contenteditable.locator('h2')).to_have_text(heading)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_blockquote(page, viewname, menubar, contenteditable):
    block = "Tiptap Block"
    contenteditable.type(block)
    expect(contenteditable.locator('p')).to_have_text(block)
    set_caret(page, contenteditable, 0)
    menu_button = menubar.locator('[richtext-click="blockquote"]')
    menu_button.click()
    expect(contenteditable.locator('blockquote > p')).to_have_text(block)
    set_caret(page, contenteditable, 5)
    expect(menu_button).to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_classbased_mark(page, viewname, menubar, contenteditable):
    lorem = "Lorem ipsum dolor sit amet."
    contenteditable.type(lorem)
    expect(contenteditable.locator('p')).to_have_text(lorem)
    select_text(page, contenteditable.locator('p'), 6, 17)
    family_menu_button = menubar.locator('[richtext-click="classBasedMark:fontFamily"]')
    family_menu_button.click()
    wait_until_idle(page)
    expect(family_menu_button.locator('+ ul[role="menu"]')).to_be_visible()
    submenu_items = family_menu_button.locator('+ ul[role="menu"] > li')
    expect(submenu_items).to_have_count(4)
    submenu_items.nth(2).click()
    wait_until_idle(page)
    expect(contenteditable.locator('p span.font-family-b')).to_have_text("ipsum dolor")
    set_caret(page, contenteditable, 8)
    expect(family_menu_button).to_have_class('active')
    expect(submenu_items.nth(2)).to_have_class('active')
    set_caret(page, contenteditable, 18)
    expect(family_menu_button).not_to_have_class('active')
    family_menu_button.click()
    for item in submenu_items.all():
        expect(item).not_to_have_class('active')
    contenteditable.click(position={'x': 5, 'y': 5})  # closes the submenu
    expect(family_menu_button.locator('+ ul[role="menu"]')).not_to_be_visible()

    # add another class to overlapping selection
    select_text(page, contenteditable.locator('p'), 12, 21)
    fontsize_menu_button = menubar.locator('[richtext-click="classBasedMark:fontSize"]')
    expect(fontsize_menu_button).not_to_have_class('active')
    fontsize_menu_button.click()
    wait_until_idle(page)
    submenu_items = fontsize_menu_button.locator('+ ul[role="menu"] > li')
    expect(submenu_items).to_have_count(4)
    submenu_items.nth(2).click()
    wait_until_idle(page)
    expect(contenteditable.locator('p span.font-family-b span.font-size-medium')).to_have_text("dolor")
    set_caret(page, contenteditable, 8)
    expect(family_menu_button).to_have_class('active')
    expect(fontsize_menu_button).not_to_have_class('active')
    set_caret(page, contenteditable, 18)
    expect(family_menu_button).not_to_have_class('active')
    expect(fontsize_menu_button).to_have_class('active')
    set_caret(page, contenteditable, 3)
    expect(family_menu_button).not_to_have_class('active')
    expect(fontsize_menu_button).not_to_have_class('active')
    fontsize_menu_button.click()
    wait_until_idle(page)
    for item in submenu_items.all():
        expect(item).not_to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_classbased_node(page, viewname, menubar, contenteditable):
    lorem = "Lorem ipsum dolor sit amet."
    contenteditable.type(lorem)
    expect(contenteditable.locator('p')).to_have_text(lorem)
    set_caret(page, contenteditable, 1)
    lineheight_menu_button = menubar.locator('[richtext-click="classBasedNode:lineHeight"]')
    lineheight_menu_button.click()
    expect(lineheight_menu_button.locator('+ ul[role="menu"]')).to_be_visible()
    submenu_items = lineheight_menu_button.locator('+ ul[role="menu"] > li')
    expect(submenu_items).to_have_count(4)
    submenu_items.nth(2).click()
    expect(contenteditable.locator('p.line-height-medium')).to_have_text("Lorem ipsum dolor sit amet.")
    expect(lineheight_menu_button).to_have_class('active')
    expect(lineheight_menu_button.locator('+ ul[role="menu"] > li').nth(2)).to_have_class('active')
    marginbottom_menu_button = menubar.locator('[richtext-click="classBasedNode:marginBottom"]')
    marginbottom_menu_button.click()
    expect(marginbottom_menu_button.locator('+ ul[role="menu"]')).to_be_visible()
    submenu_items = marginbottom_menu_button.locator('+ ul[role="menu"] > li')
    expect(submenu_items).to_have_count(4)
    submenu_items.nth(2).click()
    expect(contenteditable.locator('p.line-height-medium.margin-bottom-2')).to_have_text("Lorem ipsum dolor sit amet.")
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
    select_text(page, contenteditable.locator('p'), 6, 10)
    menu_button = menubar.locator('button[name="text.dialog_simple_link"]')
    dialog = richtext_wrapper.locator('dialog[df-induce-open=".dialog_simple_link:active"]').first
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
    select_text(page, contenteditable.locator('p'), 6, 10)
    menu_button = menubar.locator('button[name="text.dialog_simple_link"]')
    dialog = richtext_wrapper.locator('dialog[df-induce-open=".dialog_simple_link:active"]').first
    expect(dialog).not_to_be_visible()
    menu_button.click()
    expect(dialog).to_be_visible()
    text_input = dialog.locator('input[name="text"]')
    expect(text_input).to_have_value("here")
    link_input = dialog.locator('input[name="url"]')
    expect(link_input).to_have_value("")
    link_input.type("www.example.org")
    dialog.click(position={'x': 1, 'y': 1})
    placeholder = dialog.locator('input[name="url"] + [role="alert"] .dj-placeholder')
    expect(placeholder).to_have_text("Enter a valid URL.")
    dialog.locator('button[name="apply"]').click()
    expect(dialog).to_be_visible()
    dialog.click(position={'x': 1, 'y': 1})
    dialog.locator('button[name="cancel"]').click()
    expect(dialog).not_to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext_initialized'])
def test_tiptap_remove_simple_link(page, viewname, menubar, contenteditable):
    assert contenteditable.inner_html() == '<p>Click <a href="https://example.org/">here</a></p>'
    dialog = page.locator('dialog[df-induce-open=".dialog_simple_link:active"]').first
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
