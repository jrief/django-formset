import json
import pytest
from time import sleep

from django.forms import fields, forms
from django.urls import path

from formset.renderers.default import FormRenderer
from formset.collection import FormCollection
from formset.views import FormCollectionView

from .forms.contact import PhoneNumberCollection


class PersonForm(forms.Form):
    full_name = fields.CharField(
        label="Full name",
        min_length=2,
        max_length=50,
    )

    email = fields.EmailField(
        label="E-Mail",
        help_text="Please enter a valid email address",
    )


class PhoneNumberForm(forms.Form):
    phone_number = fields.RegexField(
        r'^[01+][0-9 .-]+$',
        label="Phone Number",
        min_length=2,
        max_length=20,
    )


class ContactCollectionList(FormCollection):
    min_siblings = 0
    extra_siblings = 1

    person = PersonForm()

    numbers = PhoneNumberCollection(
        renderer=FormRenderer(),
        min_siblings=1,
        max_siblings=5,
        extra_siblings=1,
    )


urlpatterns = [
    path('contacts', FormCollectionView.as_view(
        collection_class=ContactCollectionList,
        template_name='testapp/form-collection.html',
        success_url='/success',
    ), name='contacts'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contacts'])
def test_submit_data(page, mocker):
    contact_collections = page.query_selector_all('django-formset > django-form-collection')
    assert len(contact_collections) == 1
    number_collections = contact_collections[0].query_selector_all(':scope > django-form-collection')
    assert len(number_collections) == 1
    page.type('#id_0\\.person\\.full_name', "John Doe")
    page.type('#id_0\\.person\\.email', "john@example.com")
    page.type('#id_0\\.numbers\\.0\\.number\\.phone_number', "+1200300400")
    page.select_option('#id_0\\.numbers\\.0\\.number\\.label', 'work')
    spy = mocker.spy(FormCollectionView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    response = json.loads(spy.call_args.args[1].body)
    assert response == {'formset_data': [{
            'person': {'full_name': 'John Doe', 'email': 'john@example.com'}
        }, {
            'numbers': [{'number': {'phone_number': '+1200300400', 'label': 'work'}}]
        }]
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contacts'])
def test_add_inner_collection(page):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection > django-form-collection')) == 1
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="0"] > button.remove-collection:disabled')
    formset.wait_for_selector('django-form-collection > button.add-collection').click()
    assert len(formset.query_selector_all('django-form-collection > django-form-collection')) == 2
    assert len(formset.query_selector_all('django-form-collection > django-form-collection > button.remove-collection')) == 2
    assert len(formset.query_selector_all('django-form-collection > django-form-collection > button.remove-collection:disabled')) == 0
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="1"]') is not None
    formset.wait_for_selector('django-form-collection > django-form-collection[sibling-position="1"] > button.remove-collection').click()
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="1"]') is None
    formset.wait_for_selector('django-form-collection > button.add-collection').click()
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="1"]') is None
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="2"]') is not None
    page.hover('django-form-collection > django-form-collection[sibling-position="0"]')
    formset.wait_for_selector('django-form-collection > django-form-collection[sibling-position="0"] > button.remove-collection').click()
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="0"].dj-marked-for-removal') is not None
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="0"] > button.remove-collection:not(disabled)') is not None
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="2"] > button.remove-collection:disabled') is not None
    formset.wait_for_selector('django-form-collection > django-form-collection[sibling-position="0"] > button.remove-collection').click()
    assert formset.query_selector('django-form-collection > django-form-collection[sibling-position="0"]:not(.dj-marked-for-removal)') is not None
    assert len(formset.query_selector_all('django-form-collection > django-form-collection > button.remove-collection:not(disabled)')) == 2


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contacts'])
def test_add_outer_collection(page):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection')) == 2
    assert len(formset.query_selector_all(':scope > django-form-collection')) == 1
    assert len(formset.query_selector_all('django-form-collection[sibling-position="0"] > django-form-collection')) == 1
    formset.wait_for_selector('django-form-collection[sibling-position="0"] > button.add-collection').click()
    assert len(formset.query_selector_all('django-form-collection[sibling-position="0"] > django-form-collection')) == 2
    page.hover('django-form-collection[sibling-position="0"] > django-form-collection[sibling-position="0"]')
    formset.wait_for_selector('django-form-collection[sibling-position="0"] > django-form-collection[sibling-position="0"] > button.remove-collection').click()
    assert formset.query_selector('django-form-collection[sibling-position="0"] > django-form-collection[sibling-position="0"] > button.remove-collection:not(disabled)') is not None
    assert formset.query_selector('django-form-collection[sibling-position="0"] > django-form-collection[sibling-position="1"] > button.remove-collection:disabled') is not None
    formset.wait_for_selector('django-form-collection[sibling-position="0"] > button.add-collection + button.remove-collection').click()
    assert formset.query_selector('django-form-collection[sibling-position="0"] > django-form-collection[sibling-position="0"] > button.remove-collection:disabled') is not None
    assert formset.query_selector('django-form-collection[sibling-position="0"] > django-form-collection[sibling-position="1"] > button.remove-collection:disabled') is not None
    formset.wait_for_selector('django-form-collection[sibling-position="0"] > button.add-collection + button.remove-collection').click()
    assert formset.query_selector('django-form-collection[sibling-position="0"] > django-form-collection[sibling-position="0"] > button.remove-collection:not(disabled)') is not None
    assert formset.query_selector('django-form-collection[sibling-position="0"] > django-form-collection[sibling-position="1"] > button.remove-collection:not(disabled)') is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contacts'])
def test_expand_collection_template(page):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all(':scope > django-form-collection')) == 1
    formset.wait_for_selector(':scope > button.add-collection').click()
    assert len(formset.query_selector_all(':scope > django-form-collection')) == 2
    assert formset.query_selector('django-form-collection[sibling-position="1"] > form[name="1.person"]') is not None
    assert formset.query_selector('django-form-collection[sibling-position="1"] > django-form-collection[sibling-position="0"]') is not None
    assert len(formset.query_selector_all('django-form-collection[sibling-position="1"] > django-form-collection')) == 1
    formset.wait_for_selector('django-form-collection[sibling-position="1"] > button.add-collection').click()
    assert len(formset.query_selector_all('django-form-collection[sibling-position="1"] > django-form-collection')) == 2
    assert formset.query_selector('django-form-collection[sibling-position="1"] > django-form-collection[sibling-position="1"] > form[name="1.numbers.1.number"]') is not None
