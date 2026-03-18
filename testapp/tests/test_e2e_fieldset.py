import json
import pytest
from time import sleep
from playwright.sync_api import expect

from django.urls import path

from formset.views import FormView

from testapp.forms.customer import CustomerForm
from .utils import ContextMixin, get_javascript_catalog


class DemoFormView(ContextMixin, FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('customer', DemoFormView.as_view(
        form_class=CustomerForm,
        extra_context = {'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='customer'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['customer'])
def test_submit_fieldsets(page, viewname):
    fieldset = page.locator('django-formset > [role="form"] > fieldset')
    expect(fieldset).to_have_count(2)
    expect(fieldset.nth(0)).to_be_visible()
    expect(fieldset.nth(0)).to_have_attribute('name', 'billing')
    expect(fieldset.nth(0).locator('> legend')).to_have_text("Billing")
    expect(fieldset.nth(0).locator('> fieldset')).to_be_visible()
    expect(fieldset.nth(0).locator('> fieldset')).to_have_attribute('name', 'billing.address')
    expect(fieldset.nth(0).locator('> fieldset > legend')).to_have_text("Address")

    expect(fieldset.nth(1)).to_be_visible()
    expect(fieldset.nth(1)).to_have_attribute('name', 'shipping')
    expect(fieldset.nth(1).locator('> legend')).to_have_text("Shipping")
    expect(fieldset.nth(1).locator('> fieldset')).to_have_attribute('name', 'shipping.address')

    page.fill('#id_billing\\.recipient', "John Doe")
    page.fill('#id_billing\\.address\\.postal_code', "12345")
    page.fill('#id_billing\\.address\\.city', "Springfield")
    page.fill('#id_shipping\\.recipient', "Jane Doe")
    page.fill('#id_shipping\\.address\\.postal_code', "54321")
    page.fill('#id_shipping\\.address\\.city', "Shelbyville")

    with page.expect_response(page.url) as response_info:
         page.locator('django-formset button').first.click()
    assert response_info.value.ok is True
    assert response_info.value.request.post_data_json == {
        'extra_data': {},
        'formset_data': {
            'billing.recipient': "John Doe",
            'billing.address.postal_code': "12345",
            'billing.address.city': "Springfield",
            'shipping.recipient': "Jane Doe",
            'shipping.address.postal_code': "54321",
            'shipping.address.city': "Shelbyville",
            'use_billing_address': "",
        },
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['customer'])
def test_submit_hidden_fieldset(page, viewname):
    page.fill('#id_billing\\.recipient', "John Doe")
    page.fill('#id_billing\\.address\\.postal_code', "12345")
    page.fill('#id_billing\\.address\\.city', "Springfield")
    fieldset = page.locator('django-formset > [role="form"] fieldset[name="shipping"]')
    expect(fieldset).to_be_visible()
    expect(fieldset).to_have_attribute('df-hide', 'use_billing_address')
    page.click('#id_use_billing_address')
    expect(fieldset).to_be_hidden()
    with page.expect_response(page.url) as response_info:
        page.locator('django-formset button').first.click()
    assert response_info.value.ok is True
    assert response_info.value.request.post_data_json == {
        'extra_data': {},
        'formset_data': {
            'billing.recipient': "John Doe",
            'billing.address.postal_code': "12345",
            'billing.address.city': "Springfield",
            'shipping.recipient': "",
            'shipping.address.postal_code': "",
            'shipping.address.city': "",
            'use_billing_address': "on",
        },
    }
