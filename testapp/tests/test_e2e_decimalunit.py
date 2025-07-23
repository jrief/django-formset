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
        #max_digits=10,
        step_size=10,
    )


class DemoFormView(ContextMixin, FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('price_empty', DemoFormView.as_view(form_class=PriceForm), name='price_empty'),
    path('price_initial', DemoFormView.as_view(form_class=PriceForm, initial={'price': 1234560}), name='price_initial'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['price_empty'])
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
    expect(error_list).to_have_text("This field is required.")
