import pytest
from playwright.sync_api import expect

from django.forms import fields, forms
from django.urls import path

from formset.views import FormView
from formset.widgets import DecimalUnitInput

from .utils import ContextMixin, get_javascript_catalog


class DecimalUnitForm(forms.Form):
    counter = fields.IntegerField(
        widget=DecimalUnitInput(),
    )
    price = fields.DecimalField(
        widget=DecimalUnitInput(prefix='€', fixed_decimal_places=True),
        min_value=0,
        decimal_places=2,
        step_size=0.05,
    )
    ohms = fields.FloatField(
        widget=DecimalUnitInput(suffix="Ω", attrs={'decimal-places': 3}),
        min_value=0.1,
        step_size=0.1,
    )


class DemoFormView(ContextMixin, FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path(
        'fields_empty',
        DemoFormView.as_view(form_class=DecimalUnitForm),
        name='fields_empty',
    ),
    path(
        'fields_initial',
        DemoFormView.as_view(
            form_class=DecimalUnitForm,
            initial={
                'counter': 123456789,
                'price': 1234.5,
                'ohms': 123.456,
            },
        ),
        name='fields_initial',
    ),
    get_javascript_catalog(),
]


separator = " "


@pytest.fixture
def counter_field(page):
    input_field = page.locator('django-formset input[is="django-decimal-unit"][name="counter"]')
    return input_field


@pytest.fixture
def price_field(page):
    input_field = page.locator('django-formset input[is="django-decimal-unit"][name="price"]')
    return input_field


@pytest.fixture
def ohms_field(page):
    input_field = page.locator('django-formset input[is="django-decimal-unit"][name="ohms"]')
    return input_field


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_empty', 'fields_initial'])
def test_decimal_unit_required(page, viewname, price_field):
    text_box = price_field.locator('+ [role="textbox"]')
    edit_field = text_box.locator('.decimal-unit-edit [contenteditable="true"]')
    expect(price_field).not_to_be_visible()
    expect(text_box).to_be_visible()
    expect(edit_field).to_be_visible()
    expect(text_box.locator('.decimal-unit-edit .prefix')).to_contain_text("€")
    expect(text_box).not_to_have_class('focus')
    edit_field.click(position={'x': 1, 'y': 1})
    expect(text_box).to_have_class('focus')
    page.locator('django-formset').click(position={'x': 1, 'y': 1})
    expect(text_box).not_to_have_class('focus')
    error_list = price_field.locator('~ [role="alert"] .dj-errorlist')
    if viewname == 'fields_empty':
        expect(error_list).to_have_text("This field is required.")
        expect(price_field.locator(':scope:invalid')).to_have_count(1)
    elif viewname == 'fields_initial':
        expect(error_list).to_have_text("")
        expect(price_field.locator(':scope:valid')).to_have_count(1)
        expect(price_field).to_have_value("1234.50")
        expect(edit_field).to_have_text(f"1{separator}234.50")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_empty'])
def test_decimal_unit_auto_separate(page, viewname, price_field):
    edit_field = price_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
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
    expect(price_field).to_have_value("123456789")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_separate_on_delete(page, viewname, counter_field):
    edit_field = counter_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 1, 'y': 1})
    expect(edit_field).to_have_text(f"123{separator}456{separator}789")
    edit_field.press("Delete", delay=5)
    expect(edit_field).to_have_text(f"23{separator}456{separator}789")
    expect(counter_field).to_have_value("23456789")
    edit_field.press("Delete", delay=5)
    expect(edit_field).to_have_text(f"3{separator}456{separator}789")
    edit_field.press("Delete", delay=5)
    expect(edit_field).to_have_text(f"456{separator}789")
    edit_field.press("Delete", delay=5)
    expect(edit_field).to_have_text(f"56{separator}789")
    edit_field.press("Delete", delay=5)
    expect(edit_field).to_have_text(f"6{separator}789")
    edit_field.press("Delete", delay=5)
    expect(edit_field).to_have_text("789")
    edit_field.press("Delete", delay=5)
    expect(edit_field).to_have_text("89")
    edit_field.press("Delete", delay=5)
    expect(edit_field).to_have_text("9")
    edit_field.press("Delete", delay=5)
    expect(counter_field).to_have_value("")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_separate_on_backspace(page, viewname, counter_field):
    edit_field = counter_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 300, 'y': 1})
    expect(edit_field).to_have_text(f"123{separator}456{separator}789")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text(f"12{separator}345{separator}678")
    expect(counter_field).to_have_value("12345678")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text(f"1{separator}234{separator}567")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text(f"123{separator}456")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text(f"12{separator}345")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text(f"1{separator}234")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text(f"123")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text(f"12")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text(f"1")
    edit_field.press("Backspace", delay=5)
    expect(edit_field).to_have_text("")
    expect(counter_field).to_have_value("")


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
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_separate_on_move_right(page, viewname, counter_field):
    edit_field = counter_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 1, 'y': 1})
    assert get_caret_position(edit_field) == 0
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 1
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 2
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 4
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 5
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 6
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 8
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 9
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 10
    edit_field.press("ArrowRight", delay=5)
    assert get_caret_position(edit_field) == 11


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_separate_on_move_left(page, viewname, counter_field):
    edit_field = counter_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 300, 'y': 1})
    assert get_caret_position(edit_field) == 11
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 10
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 9
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 8
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 6
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 5
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 4
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 2
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 1
    edit_field.press("ArrowLeft", delay=5)
    assert get_caret_position(edit_field) == 0


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('locale', ['en-US', 'de-DE'])
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_locale_settings(page, locale, viewname, ohms_field):
    edit_field = ohms_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    if locale == 'en-US':
        expect(edit_field).to_have_text(f"123.456")
    elif locale == 'de-DE':
        expect(edit_field).to_have_text(f"123,456")
    expect(ohms_field).to_have_value('123.456')
    edit_field.click(position={'x': 300, 'y': 1})
    edit_field.press("Backspace", delay=5)
    edit_field.press("Backspace", delay=5)
    edit_field.press("Backspace", delay=5)
    edit_field.press("Backspace", delay=5)
    if locale == 'en-US':
        edit_field.type(",78")
        expect(edit_field).to_have_text(f"123.78")
    elif locale == 'de-DE':
        edit_field.type(".78")
        expect(edit_field).to_have_text(f"123,78")
    expect(ohms_field).to_have_value('123.78')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_unsteppable(page, viewname, counter_field):
    edit_field = counter_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 1, 'y': 1})
    edit_field.press("ArrowUp", delay=5)
    expect(edit_field).to_have_text(f"123{separator}456{separator}789")
    expect(counter_field).to_have_value('123456789')
    edit_field.press("ArrowDown", delay=5)
    expect(edit_field).to_have_text(f"123{separator}456{separator}789")
    expect(counter_field).to_have_value('123456789')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_step_up(page, viewname, price_field):
    edit_field = price_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 1, 'y': 1})
    edit_field.press("ArrowUp", delay=5)
    expect(edit_field).to_have_text(f"1{separator}234.55")
    expect(price_field).to_have_value('1234.55')
    edit_field.press("ArrowUp", delay=5)
    expect(edit_field).to_have_text(f"1{separator}234.60")
    expect(price_field).to_have_value('1234.60')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_step_down(page, viewname, price_field):
    edit_field = price_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 1, 'y': 1})
    edit_field.press("ArrowDown", delay=5)
    expect(edit_field).to_have_text(f"1{separator}234.45")
    expect(price_field).to_have_value('1234.45')
    edit_field.press("ArrowDown", delay=5)
    expect(edit_field).to_have_text(f"1{separator}234.40")
    expect(price_field).to_have_value('1234.40')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_initial'])
def test_decimal_unit_round(page, viewname, ohms_field):
    edit_field = ohms_field.locator('+ [role="textbox"] .decimal-unit-edit [contenteditable="true"]')
    edit_field.click(position={'x': 300, 'y': 1})
    expect(edit_field).to_have_text("123.456")
    expect(ohms_field).to_have_value('123.456')
    edit_field.type("7")
    expect(edit_field).to_have_text("123.457")
    expect(ohms_field).to_have_value('123.457')
    edit_field.type("4")
    expect(edit_field).to_have_text("123.457")
    expect(ohms_field).to_have_value('123.457')
    edit_field.type("5")
    expect(edit_field).to_have_text("123.458")
    expect(ohms_field).to_have_value('123.458')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['fields_empty'])
def test_decimal_unit_prefix_suffix(page, viewname, price_field, ohms_field):
    text_box = price_field.locator('+ [role="textbox"]')
    expect(text_box.locator('.prefix')).to_have_text("€")
    expect(text_box.locator('.suffix')).not_to_be_visible()
    text_box = ohms_field.locator('+ [role="textbox"]')
    expect(text_box.locator('.prefix')).not_to_be_visible()
    expect(text_box.locator('.suffix')).to_have_text("Ω")
