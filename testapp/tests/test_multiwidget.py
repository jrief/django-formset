import pytest
from bs4 import BeautifulSoup

from formset.renderers.default import FormRenderer as DefaultFormRenderer
from formset.renderers.bootstrap import FormRenderer as BootstrapFormRenderer
from formset.renderers.bulma import FormRenderer as BulmaFormRenderer
from formset.renderers.tailwind import FormRenderer as TailwindFormRenderer
from formset.renderers.uikit import FormRenderer as UIKitFormRenderer

from testapp.forms.multiwidget import MultiWidgetForm, PhoneWidget, PriceWidget

VALID_DATA = {
    'name': 'Alice',
    'phone_numbers_0': '555',
    'phone_numbers_1': '123',
    'phone_numbers_2': '4567',
    'price_0': '99.99',
    'price_1': 'EUR',
}


def render_widget(widget, name, value, renderer):
    context = widget.get_context(name, value, {})
    html = widget._render(widget.template_name, context, renderer)
    return BeautifulSoup(html, features='html.parser')


# ---------------------------------------------------------------------------
# Rendering — CSS classes applied to MultiWidget sub-widgets
# ---------------------------------------------------------------------------

class TestMultiWidgetCSSRendering:
    """
    Verify _amend_multiwidget() applies framework CSS classes to sub-widgets.
    Before the fix, {% include %} in multiwidget.html bypassed renderer.render()
    so _context_modifiers were never called for sub-widget templates.
    """

    # --- Bootstrap ---

    def test_bootstrap_phone_inputs_get_form_control(self):
        soup = render_widget(PhoneWidget(), 'phone_numbers', None, BootstrapFormRenderer())
        inputs = soup.find_all('input')
        assert len(inputs) == 3
        for inp in inputs:
            assert 'form-control' in inp.get('class', []), \
                f"Missing 'form-control' on {inp.get('id')}"

    def test_bootstrap_price_textinput_gets_form_control(self):
        soup = render_widget(PriceWidget(), 'price', None, BootstrapFormRenderer())
        amount = soup.find('input')
        assert amount is not None
        assert 'form-control' in amount.get('class', [])

    def test_bootstrap_price_select_gets_form_select(self):
        soup = render_widget(PriceWidget(), 'price', None, BootstrapFormRenderer())
        select = soup.find('select')
        assert select is not None
        assert 'form-select' in select.get('class', [])

    # --- Bulma ---

    def test_bulma_phone_inputs_get_input_class(self):
        soup = render_widget(PhoneWidget(), 'phone_numbers', None, BulmaFormRenderer())
        for inp in soup.find_all('input'):
            assert 'input' in inp.get('class', [])

    def test_bulma_price_textinput_gets_input_class(self):
        soup = render_widget(PriceWidget(), 'price', None, BulmaFormRenderer())
        amount = soup.find('input')
        assert amount is not None
        assert 'input' in amount.get('class', [])

    # --- UIkit ---

    def test_uikit_phone_inputs_get_uk_input(self):
        soup = render_widget(PhoneWidget(), 'phone_numbers', None, UIKitFormRenderer())
        for inp in soup.find_all('input'):
            assert 'uk-input' in inp.get('class', [])

    def test_uikit_price_select_gets_uk_select(self):
        soup = render_widget(PriceWidget(), 'price', None, UIKitFormRenderer())
        select = soup.find('select')
        assert select is not None
        assert 'uk-select' in select.get('class', [])

    # --- Tailwind ---

    def test_tailwind_phone_inputs_get_formset_text_input(self):
        soup = render_widget(PhoneWidget(), 'phone_numbers', None, TailwindFormRenderer())
        for inp in soup.find_all('input'):
            assert 'formset-text-input' in inp.get('class', [])

    def test_tailwind_price_select_gets_formset_select(self):
        soup = render_widget(PriceWidget(), 'price', None, TailwindFormRenderer())
        select = soup.find('select')
        assert select is not None
        assert 'formset-select' in select.get('class', [])

    # --- Default (no framework classes, must not raise) ---

    def test_default_renderer_renders_without_error(self):
        soup = render_widget(PhoneWidget(), 'phone_numbers', None, DefaultFormRenderer())
        assert len(soup.find_all('input')) == 3

    def test_default_renderer_price_mixed_widget_renders_without_error(self):
        soup = render_widget(PriceWidget(), 'price', None, DefaultFormRenderer())
        assert soup.find('input') is not None
        assert soup.find('select') is not None


# ---------------------------------------------------------------------------
# Form validation — data submitted as separate MultiWidget keys
# ---------------------------------------------------------------------------

class TestMultiWidgetFormValidation:
    """
    Verify the form validates correctly when data arrives in Django's
    MultiWidget format (fieldname_0, fieldname_1, …), which is what
    aggregateValues() now emits after the FieldGroup fix.
    """

    def test_valid_data_passes(self):
        form = MultiWidgetForm(data=VALID_DATA)
        assert form.is_valid(), form.errors

    def test_phone_field_compress_joins_with_dash(self):
        form = MultiWidgetForm(data=VALID_DATA)
        assert form.is_valid()
        assert form.cleaned_data['phone_numbers'] == '555-123-4567'

    def test_price_field_compress_joins_amount_and_currency(self):
        form = MultiWidgetForm(data=VALID_DATA)
        assert form.is_valid()
        assert form.cleaned_data['price'] == '99.99 EUR'

    def test_missing_phone_parts_fails_validation(self):
        data = {**VALID_DATA, 'phone_numbers_0': '', 'phone_numbers_1': '', 'phone_numbers_2': ''}
        form = MultiWidgetForm(data=data)
        assert not form.is_valid()
        assert 'phone_numbers' in form.errors

    def test_missing_price_amount_fails_validation(self):
        data = {**VALID_DATA, 'price_0': ''}
        form = MultiWidgetForm(data=data)
        assert not form.is_valid()
        assert 'price' in form.errors

    def test_invalid_price_amount_type_fails_validation(self):
        data = {**VALID_DATA, 'price_0': 'not-a-number'}
        form = MultiWidgetForm(data=data)
        assert not form.is_valid()
        assert 'price' in form.errors
