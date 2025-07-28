import pytest
from playwright.sync_api import expect

from django.forms import fields, forms
from django.urls import path

from formset.views import FormView
from formset.widgets import DecimalUnitInput

from .utils import ContextMixin, get_javascript_catalog


class PriceForm(forms.Form):
    price = fields.DecimalField(
        label="Price",
        widget=DecimalUnitInput(prefix='€'),
        min_value=-1000,
        decimal_places=2,
        step_size=0.01,
    )


class DemoFormView(ContextMixin, FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('price_empty', DemoFormView.as_view(form_class=PriceForm), name='price_empty'),
    path('price_integer', DemoFormView.as_view(form_class=PriceForm, initial={'price': 1234560}), name='price_integer'),
    path('price_float', DemoFormView.as_view(form_class=PriceForm, initial={'price': 12345.60}), name='price_float'),
    get_javascript_catalog(),
]


separator = " "


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['price_empty', 'price_integer', 'price_float'])
def test_decimal_unit_required(page, viewname):
    input_field = page.locator('django-formset input[is="django-decimal-unit"]')
    text_box = input_field.locator('+ [role="textbox"]')
    edit_field = text_box.locator('.decimal-unit-edit [contenteditable="true"]')
    expect(input_field).not_to_be_visible()
    expect(text_box).to_be_visible()
    expect(edit_field).to_be_visible()
    expect(text_box.locator('.decimal-unit-edit .prefix')).to_contain_text("€")
    expect(text_box).not_to_have_class('focus')
    edit_field.click(position={'x': 1, 'y': 1})
    expect(text_box).to_have_class('focus')
    page.locator('django-formset').click(position={'x': 1, 'y': 1})
    expect(text_box).not_to_have_class('focus')
    error_list = input_field.locator('~ [role="alert"] .dj-errorlist')
    if viewname == 'price_empty':
        expect(error_list).to_have_text("This field is required.")
        expect(input_field.locator(':scope:invalid')).to_have_count(1)
    elif viewname in ['price_integer', 'price_float']:
        expect(error_list).to_have_text("")
        expect(input_field.locator(':scope:valid')).to_have_count(1)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['price_empty'])
def test_decimal_unit_auto_separate(page, viewname):
    input_field = page.locator('django-formset input[is="django-decimal-unit"]')
    edit_field = input_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 1, 'y': 1})
    edit_field.type("12")
    expect(edit_field).to_have_text("12")
    edit_field.type("3")
    expect(edit_field).to_have_text("123")
    edit_field.type("4")
    expect(edit_field).to_have_text(f"1{separator}234")
    edit_field.type("5")
    expect(edit_field).to_have_text(f"12{separator}345")
    edit_field.type("6")
    expect(edit_field).to_have_text(f"123{separator}456")
    edit_field.type("7")
    expect(edit_field).to_have_text(f"1{separator}234{separator}567")
    edit_field.type("8")
    expect(edit_field).to_have_text(f"12{separator}345{separator}678")
    edit_field.type("9")
    expect(edit_field).to_have_text(f"123{separator}456{separator}789")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['price_integer'])
def test_decimal_unit_separate_on_delete(page, viewname):
    input_field = page.locator('django-formset input[is="django-decimal-unit"]')
    edit_field = input_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 1, 'y': 1})
    expect(edit_field).to_have_text(f"1{separator}234{separator}560")
    edit_field.press("Delete")
    expect(edit_field).to_have_text(f"234{separator}560")
    edit_field.press("Delete")
    expect(edit_field).to_have_text(f"34{separator}560")
    edit_field.press("Delete")
    expect(edit_field).to_have_text(f"4{separator}560")
    edit_field.press("Delete")
    expect(edit_field).to_have_text("560")
    edit_field.press("Delete")
    expect(edit_field).to_have_text("60")
    edit_field.press("Delete")
    expect(edit_field).to_have_text("0")
    edit_field.press("Delete")
    expect(edit_field).to_have_text("")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['price_integer'])
def test_decimal_unit_separate_on_backspace(page, viewname):
    input_field = page.locator('django-formset input[is="django-decimal-unit"]')
    edit_field = input_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 300, 'y': 1})
    expect(edit_field).to_have_text(f"1{separator}234{separator}560")
    edit_field.press("Backspace")
    expect(edit_field).to_have_text(f"123{separator}456")
    edit_field.press("Backspace")
    expect(edit_field).to_have_text(f"12{separator}345")
    edit_field.press("Backspace")
    expect(edit_field).to_have_text(f"1{separator}234")
    edit_field.press("Backspace")
    expect(edit_field).to_have_text("123")
    edit_field.press("Backspace")
    expect(edit_field).to_have_text("12")
    edit_field.press("Backspace")
    expect(edit_field).to_have_text("1")
    edit_field.press("Backspace")
    expect(edit_field).to_have_text("")


def get_caret_position(edit_field):
    caret_pos = edit_field.evaluate("""
    (el) => {
        const selection = window.getSelection();
        let caretOffset = 0;
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            const preCaretRange = range.cloneRange();
            preCaretRange.selectNodeContents(el);
            preCaretRange.setEnd(range.endContainer, range.endOffset);
            caretOffset = preCaretRange.toString().length;
        }
        return caretOffset;
    }
    """)
    return caret_pos


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['price_integer'])
def test_decimal_unit_separate_on_move_right(page, viewname):
    input_field = page.locator('django-formset input[is="django-decimal-unit"]')
    edit_field = input_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 1, 'y': 1})
    # 1 234 560
    assert get_caret_position(edit_field) == 0
    edit_field.press("ArrowRight")
    assert get_caret_position(edit_field) == 2
    edit_field.press("ArrowRight")
    assert get_caret_position(edit_field) == 3
    edit_field.press("ArrowRight")
    assert get_caret_position(edit_field) == 4
    edit_field.press("ArrowRight")
    assert get_caret_position(edit_field) == 6
    edit_field.press("ArrowRight")
    assert get_caret_position(edit_field) == 7
    edit_field.press("ArrowRight")
    assert get_caret_position(edit_field) == 8
    edit_field.press("ArrowRight")
    assert get_caret_position(edit_field) == 9


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['price_integer'])
def test_decimal_unit_separate_on_move_left(page, viewname):
    input_field = page.locator('django-formset input[is="django-decimal-unit"]')
    edit_field = input_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 300, 'y': 1})
    # 1 234 560
    assert get_caret_position(edit_field) == 9
    edit_field.press("ArrowLeft")
    assert get_caret_position(edit_field) == 8
    edit_field.press("ArrowLeft")
    assert get_caret_position(edit_field) == 7
    edit_field.press("ArrowLeft")
    assert get_caret_position(edit_field) == 6
    edit_field.press("ArrowLeft")
    assert get_caret_position(edit_field) == 4
    edit_field.press("ArrowLeft")
    assert get_caret_position(edit_field) == 3
    edit_field.press("ArrowLeft")
    assert get_caret_position(edit_field) == 2
    edit_field.press("ArrowLeft")
    assert get_caret_position(edit_field) == 0
