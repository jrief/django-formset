import json
import pytest

from django.urls import path

from formset.views import FormCollectionView

from testapp.forms.customer import CustomerCollection


urlpatterns = [
    path('customer', FormCollectionView.as_view(
        collection_class=CustomerCollection,
        template_name='testapp/form-collection.html',
        success_url='/success',
    ), name='customer'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['customer'])
def test_submit_customer(page, mocker):
    customer_collections = page.query_selector_all('django-formset > django-form-collection')
    assert len(customer_collections) == 2
    fieldset = customer_collections[0].query_selector('fieldset[hide-if]')
    assert fieldset is not None
    legend = fieldset.query_selector('legend')
    assert legend.text_content() == "Customer"
    assert customer_collections[1].query_selector('fieldset') is None
    page.type('#id_customer\\.name', "John Doe")
    page.type('#id_customer\\.address', "123, Lye Street")
    spy = mocker.spy(FormCollectionView, 'post')
    page.query_selector('django-formset button').click()
    response = json.loads(spy.call_args.args[1].body)
    assert response == {'formset_data': {
        'customer': {'name': "John Doe", 'address': "123, Lye Street", 'phone_number': ""},
        'register': {'no_customer': ""}
    }}


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['customer'])
def test_submit_no_customer(page, mocker):
    assert page.query_selector('django-formset > django-form-collection:first-of-type fieldset[hide-if]') is not None
    page.click('#id_register\\.no_customer')
    assert page.query_selector('django-formset > django-form-collection:first-of-type fieldset[hidden]') is not None
    spy = mocker.spy(FormCollectionView, 'post')
    page.query_selector('django-formset button').click()
    response = json.loads(spy.call_args.args[1].body)
    assert response == {'formset_data': {
        'customer': {'name': "", 'address': "", 'phone_number': ""},
        'register': {'no_customer': "on"}
    }}
