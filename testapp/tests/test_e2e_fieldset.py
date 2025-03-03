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
def test_submit_fieldsets(page, mocker, viewname):
    fieldset = page.locator('django-formset > .dj-form fieldset')
    expect(fieldset).to_have_count(2)
    expect(fieldset.nth(0)).to_be_visible()
    expect(fieldset.nth(1)).to_be_visible()
    expect(fieldset.nth(0)).to_have_attribute('name', 'billing_address')
    expect(fieldset.nth(1)).to_have_attribute('name', 'shipping_address')
    expect(fieldset.nth(0).locator('legend')).to_have_text("Billing Address")
    expect(fieldset.nth(1).locator('legend')).to_have_text("Shipping Address")
    page.fill('#id_billing_address\\.recipient', "John Doe")
    page.fill('#id_billing_address\\.postal_code', "12345")
    page.fill('#id_billing_address\\.city', "Springfield")
    page.fill('#id_shipping_address\\.recipient', "Jane Doe")
    page.fill('#id_shipping_address\\.postal_code', "54321")
    page.fill('#id_shipping_address\\.city', "Shelbyville")
    spy = mocker.spy(DemoFormView, 'post')
    page.locator('django-formset button').first.click()
    sleep(0.25)
    expected = {'formset_data': {
        'billing_address.recipient': "John Doe",
        'billing_address.postal_code': "12345",
        'billing_address.city': "Springfield",
        'shipping_address.recipient': "Jane Doe",
        'shipping_address.postal_code': "54321",
        'shipping_address.city': "Shelbyville",
        'use_billing_address': "",
    }}
    spy.assert_called()
    response = json.loads(spy.call_args.args[1].body)
    assert response == expected


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['customer'])
def test_submit_hidden_fieldset(page, mocker, viewname):
    page.fill('#id_billing_address\\.recipient', "John Doe")
    page.fill('#id_billing_address\\.postal_code', "12345")
    page.fill('#id_billing_address\\.city', "Springfield")
    fieldset = page.locator('django-formset > .dj-form fieldset[name="shipping_address"]')
    expect(fieldset).to_be_visible()
    expect(fieldset).to_have_attribute('df-hide', 'use_billing_address')
    page.click('#id_use_billing_address')
    expect(fieldset).to_be_hidden()
    spy = mocker.spy(DemoFormView, 'post')
    page.locator('django-formset button').first.click()
    sleep(0.25)
    expected = {'formset_data': {
        'billing_address.recipient': "John Doe",
        'billing_address.postal_code': "12345",
        'billing_address.city': "Springfield",
        'shipping_address.recipient': "",
        'shipping_address.postal_code': "",
        'shipping_address.city': "",
        'use_billing_address': "on",
    }}
    spy.assert_called()
    response = json.loads(spy.call_args.args[1].body)
    assert response == expected
