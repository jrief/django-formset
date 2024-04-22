import json
import pytest
from time import sleep
from playwright.sync_api import expect

from django.urls import path

from formset.views import FormCollectionView

from testapp.forms.customer import CustomerCollection


urlpatterns = [
    path('customer', FormCollectionView.as_view(
        collection_class=CustomerCollection,
        template_name='testapp/form-collection.html',
        success_url='/success',
        extra_context = {'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='customer'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['customer'])
def test_submit_customer(page, mocker, viewname):
    customer_collections = page.locator('django-formset > django-form-collection')
    expect(customer_collections).to_have_count(2)
    fieldset = customer_collections.first.locator('fieldset[df-hide]')
    expect(fieldset).to_be_visible()
    legend = fieldset.locator('legend')
    expect(legend).to_have_text("Customer")
    expect(customer_collections.last.locator('fieldset')).not_to_be_visible()
    page.fill('#id_customer\\.name', "John Doe")
    page.fill('#id_customer\\.address', "123, Lye Street")
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset button').first.click()
    sleep(0.25)
    spy.assert_called()
    response = json.loads(spy.call_args.args[1].body)
    assert response == {'formset_data': {
        'customer': {'name': "John Doe", 'address': "123, Lye Street", 'phone_number': ""},
        'register': {'no_customer': ""}
    }}


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['customer'])
def test_submit_no_customer(page, mocker, viewname):
    fieldset = page.locator('django-formset > django-form-collection fieldset')
    expect(fieldset).to_have_attribute('df-hide', 'register.no_customer')
    page.locator('#id_register\\.no_customer').click()
    expect(fieldset).to_be_hidden()
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset button').first.click()
    sleep(0.25)
    spy.assert_called()
    response = json.loads(spy.call_args.args[1].body)
    assert response == {'formset_data': {
        'customer': {'name': "", 'address': "", 'phone_number': ""},
        'register': {'no_customer': "on"}
    }}
