import pytest
from playwright.sync_api import expect
from time import sleep

from django.forms import fields, forms
from django.urls import path

from formset.richtext import controls
from formset.richtext.widgets import RichTextarea
from formset.views import FormView


control_elements = [
    controls.Heading([1,2,3]),
    controls.Bold(),
    controls.Italic(),
    controls.Underline(),
    controls.Link(),
    controls.HorizontalRule(),
    controls.Separator(),
    controls.Redo(),
    controls.Undo(),
]

class PlainRichTextForm(forms.Form):
    text = fields.CharField(
        widget=RichTextarea(control_elements=control_elements),
    )


class JSONRichTextForm(forms.Form):
    text = fields.JSONField(
        widget=RichTextarea(control_elements=control_elements),
    )


class DemoFormView(FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('plain_richtext', DemoFormView.as_view(
        form_class=PlainRichTextForm,
    ), name='plain_richtext'),
    path('plain_richtext_initialized', DemoFormView.as_view(
        form_class=PlainRichTextForm,
        initial={'text': '<p>Click <a href="https://example.org">here</a></p>'},
    ), name='plain_richtext_initialized'),
    path('json_richtext', DemoFormView.as_view(
        form_class=JSONRichTextForm,
    ), name='json_richtext'),
]


@pytest.fixture
def richtext_wrapper(page):
    return page.locator('.dj-richtext-wrapper')


@pytest.fixture
def menubar(richtext_wrapper):
    menubar = richtext_wrapper.locator('[role="menubar"]')
    menubar.element_handle() is not None
    return menubar


@pytest.fixture
def contenteditable(richtext_wrapper):
    contenteditable = richtext_wrapper.locator('[contenteditable="true"]')
    assert contenteditable.element_handle() is not None
    return contenteditable


def select_text(paragraph, start, end):
    paragraph.evaluate(f'''paragraph => {{
        const selection = window.getSelection();
        const range = document.createRange();
        selection.removeAllRanges();
        range.setStart(paragraph.childNodes[0], {start});
        range.setEnd(paragraph.childNodes[0], {end});
        selection.addRange(range);
    }}''')


def set_caret(page, position):
    page.keyboard.press('Home')
    for _ in range(position):
        page.keyboard.press('ArrowRight')


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
    contenteditable.click(position={'x': 2, 'y': 2})
    set_caret(page, 9)
    expect(button).to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_heading(page, viewname, menubar, contenteditable):
    heading = "Tiptap Editor"
    contenteditable.type(heading)
    assert contenteditable.inner_html() == f"<p>{heading}</p>"
    set_caret(page, 0)
    menu_button = menubar.locator('[richtext-click="heading"]')
    submenu = menubar.locator('[richtext-click="heading"] + ul[role="menu"]')
    expect(submenu).not_to_be_visible()
    menu_button.click()
    expect(submenu).to_be_visible()
    submenu.locator('[richtext-click="heading:1"]').click()
    assert contenteditable.inner_html() == f"<h1>{heading}</h1>"
    contenteditable.click(position={'x': 100, 'y': 20})
    set_caret(page, 5)
    expect(menu_button).to_have_class('active')
    expect(submenu).not_to_be_visible()
    menu_button.click()
    expect(submenu).to_be_visible()
    expect(submenu.locator('li:first-child')).to_have_class('active')
    expect(submenu.locator('li:nth-child(2)')).not_to_have_class('active')
    expect(submenu.locator('li:nth-child(3)')).not_to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_valid_link(page, viewname, menubar, contenteditable):
    clickme = "Click here"
    contenteditable.type(clickme)
    assert contenteditable.inner_html() == f"<p>{clickme}</p>"
    select_text(contenteditable.locator('p'), 6, 10)
    menu_button = menubar.locator('[richtext-click="link"]')
    dialog = page.locator('dialog[richtext-opener="link"]')
    expect(dialog).not_to_be_visible()
    menu_button.click()
    sleep(0.25)
    expect(dialog).to_be_visible()
    text_input = dialog.locator('input[name="text"]')
    expect(text_input).to_have_value("here")
    link_input = dialog.locator('input[name="url"]')
    expect(link_input).to_have_value("")
    link_input.type("https://example.org/")
    expect(link_input).to_have_value("https://example.org/")
    save_button = dialog.locator('button[name="save"]')
    save_button.click()
    sleep(0.25)
    expect(dialog).not_to_be_visible()
    assert contenteditable.inner_html() == '<p>Click <a target="_blank" rel="noopener noreferrer nofollow" href="https://example.org/">here</a></p>'
    set_caret(page, 9)
    expect(menu_button).to_have_class('active')
    set_caret(page, 3)
    set_caret(page, 2)
    expect(menu_button).not_to_have_class('active')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext', 'json_richtext'])
def test_tiptap_invalid_link(page, viewname, menubar, contenteditable):
    clickme = "Click here"
    contenteditable.type(clickme)
    assert contenteditable.inner_html() == f"<p>{clickme}</p>"
    select_text(contenteditable.locator('p'), 6, 10)
    menu_button = menubar.locator('[richtext-click="link"]')
    dialog = page.locator('dialog[richtext-opener="link"]')
    expect(dialog).not_to_be_visible()
    menu_button.click()
    expect(dialog).to_be_visible()
    text_input = dialog.locator('input[name="text"]')
    expect(text_input).to_have_value("here")
    link_input = dialog.locator('input[name="url"]')
    expect(link_input).to_have_value("")
    link_input.type("www.example.org")
    dialog.click(position={'x': 1, 'y': 1})
    placeholder = dialog.locator('#id_dialog_edit_link-url + .dj-field-errors .dj-placeholder')
    expect(placeholder).to_have_text("Enter a valid URL.")
    dialog.locator('button[name="save"]').click()
    expect(dialog).to_be_visible()
    dialog.locator('button[name="close"]').click()
    sleep(0.1)
    expect(dialog).not_to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['plain_richtext_initialized'])
def test_tiptap_remove_link(page, viewname, menubar, contenteditable):
    assert contenteditable.inner_html() == '<p>Click <a target="_blank" rel="noopener noreferrer nofollow" href="https://example.org">here</a></p>'
    select_text(contenteditable.locator('p > a'), 0, 4)
    menu_button = menubar.locator('[richtext-click="link"]')
    dialog = page.locator('dialog[richtext-opener="link"]')
    expect(dialog).not_to_be_visible()
    menu_button.click()
    expect(dialog).to_be_visible()
    text_input = dialog.locator('input[name="text"]')
    expect(text_input).to_have_value("here")
    link_input = dialog.locator('input[name="url"]')
    expect(link_input).to_have_value("https://example.org")
    dialog.locator('button[name="remove"]').click()
    sleep(0.1)
    expect(dialog).not_to_be_visible()
    contenteditable.inner_html() == '<p>Click here</p>'
