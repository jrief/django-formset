import json
import pytest

from time import sleep

from django.forms import fields, forms
from django.urls import path

from formset.collection import FormCollection
from formset.views import FormCollectionView

from testapp.forms.contact import PhoneNumberCollection


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
        r'^[01+][ 0-9.\-]+$',
        label="Phone Number",
        min_length=2,
        max_length=20,
    )


class SortedContactCollection(FormCollection):
    person = PersonForm()

    numbers = PhoneNumberCollection(
        min_siblings=0,
        is_sortable=True,
        initial=[
            {'number': {'phone_number': "+1 234 567 8900"}},
            {'number': {'phone_number': "+33 1 43478293"}},
            {'number': {'phone_number': "+39 335 327041"}},
            {'number': {'phone_number': "+41 91 667914"}},
            {'number': {'phone_number': "+49 89 7178864"}},
        ],
    )


class ContactCollectionList(FormCollection):
    min_siblings = 0
    extra_siblings = 1

    person = PersonForm()

    numbers = PhoneNumberCollection(
        min_siblings=1,
        max_siblings=5,
        extra_siblings=1,
    )


class SortedContactCollectionList(ContactCollectionList):
    is_sortable = True

    numbers = PhoneNumberCollection(
        min_siblings=1,
        max_siblings=5,
        extra_siblings=1,
        is_sortable=True,
    )


urlpatterns = [
    path('contactlist', FormCollectionView.as_view(
        collection_class=ContactCollectionList,
        template_name='testapp/form-collection.html',
        success_url='/success',
    ), name='contactlist'),
    path('sortedcontactlist', FormCollectionView.as_view(
        collection_class=SortedContactCollectionList,
        template_name='testapp/form-collection.html',
        success_url='/success',
    ), name='sortedcontactlist'),
    path('sortedcontact', FormCollectionView.as_view(
        collection_class=SortedContactCollection,
        template_name='testapp/form-collection.html',
        extra_context={'force_submission': True},
        success_url='/success',
    ), name='sortedcontact'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contactlist', 'sortedcontactlist'])
def test_submit_data(page, mocker, viewname):
    contact_collections = page.query_selector_all('django-formset > .collection-siblings > django-form-collection')
    assert len(contact_collections) == 1
    number_collections = contact_collections[0].query_selector_all(':scope > .collection-siblings > django-form-collection')
    assert len(number_collections) == 1
    page.fill('#id_0\\.person\\.full_name', "John Doe")
    page.fill('#id_0\\.person\\.email', "john@example.com")
    page.fill('#id_0\\.numbers\\.0\\.number\\.phone_number', "+1200300400")
    page.select_option('#id_0\\.numbers\\.0\\.number\\.label', 'work')
    spy = mocker.spy(FormCollectionView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {'formset_data': [{
        'person': {'full_name': 'John Doe', 'email': 'john@example.com'},
        'numbers': [{'number': {'phone_number': '+1200300400', 'label': 'work'}}],
    }]}


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contactlist', 'sortedcontactlist'])
def test_add_inner_collection(page):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection > .collection-siblings > django-form-collection')) == 1
    assert formset.query_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"] > button.remove-collection:disabled')
    formset.wait_for_selector('django-form-collection > .collection-siblings > button.add-collection').click()
    assert len(formset.query_selector_all('django-form-collection > .collection-siblings > django-form-collection')) == 2
    assert len(formset.query_selector_all('django-form-collection > .collection-siblings > django-form-collection > button.remove-collection')) == 2
    assert len(formset.query_selector_all('django-form-collection > .collection-siblings > django-form-collection > button.remove-collection:disabled')) == 0
    assert formset.query_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="1"]') is not None
    formset.wait_for_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="1"] > button.remove-collection').click()
    assert formset.query_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="1"]') is None
    formset.wait_for_selector('django-form-collection > .collection-siblings > button.add-collection').click()
    assert formset.query_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="1"]') is not None
    page.hover('django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"]')
    formset.wait_for_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"] > button.remove-collection').click()
    assert formset.query_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"].dj-marked-for-removal') is not None
    assert formset.query_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"] > button.remove-collection:not(disabled)') is not None
    assert formset.query_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="1"] > button.remove-collection:disabled') is not None
    formset.wait_for_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"] > button.remove-collection').click()
    assert formset.query_selector('django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"]:not(.dj-marked-for-removal)') is not None
    assert len(formset.query_selector_all('django-form-collection > .collection-siblings > django-form-collection > button.remove-collection:not(disabled)')) == 2


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contactlist', 'sortedcontactlist'])
def test_add_outer_collection(page, viewname):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all('django-form-collection')) == 2
    assert len(formset.query_selector_all(':scope > .collection-siblings > django-form-collection')) == 1
    assert len(formset.query_selector_all('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection')) == 1
    formset.wait_for_selector('django-form-collection[sibling-position="0"] > .collection-siblings > button.add-collection').click()
    assert len(formset.query_selector_all('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection')) == 2
    page.hover('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="0"]')
    formset.wait_for_selector('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="0"] > button.remove-collection').click()
    assert formset.query_selector('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="0"] > button.remove-collection:not(disabled)') is not None
    assert formset.query_selector('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="1"] > button.remove-collection:disabled') is not None
    formset.wait_for_selector('django-form-collection[sibling-position="0"] > .collection-siblings + button.remove-collection').click()
    assert formset.query_selector('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="0"] > button.remove-collection:not(disabled)') is not None
    assert formset.query_selector('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="1"] > button.remove-collection:disabled') is not None
    formset.wait_for_selector('django-form-collection[sibling-position="0"] > .collection-siblings + button.remove-collection').click()
    assert formset.query_selector('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="0"] > button.remove-collection:not(disabled)') is not None
    assert formset.query_selector('django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="1"] > button.remove-collection:not(disabled)') is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contactlist', 'sortedcontactlist'])
def test_expand_collection_template(page, viewname):
    formset = page.query_selector('django-formset')
    assert len(formset.query_selector_all(':scope > .collection-siblings > django-form-collection')) == 1
    formset.wait_for_selector(':scope > .collection-siblings > button.add-collection').click()
    assert len(formset.query_selector_all(':scope > .collection-siblings > django-form-collection')) == 2
    assert formset.query_selector('django-form-collection[sibling-position="1"] > form[name="1.person"]') is not None
    assert formset.query_selector('django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection[sibling-position="0"]') is not None
    assert len(formset.query_selector_all('django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection')) == 1
    formset.wait_for_selector('django-form-collection[sibling-position="1"] > .collection-siblings > button.add-collection').click()
    assert len(formset.query_selector_all('django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection')) == 2
    assert formset.query_selector('django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection[sibling-position="1"] > form[name="1.numbers.1.number"]') is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['sortedcontactlist'])
def test_submit_reordered_data(page, mocker):
    contact_collections = page.locator('django-formset > .collection-siblings > django-form-collection')
    assert contact_collections.count() == 1
    number_collections = contact_collections.first.locator(':scope > .collection-siblings > django-form-collection')
    assert number_collections.count() == 1
    page.fill('#id_0\\.person\\.full_name', "Margret First")
    page.fill('#id_0\\.person\\.email', "margret@example.com")
    page.fill('#id_0\\.numbers\\.0\\.number\\.phone_number', "+1200300400")
    page.select_option('#id_0\\.numbers\\.0\\.number\\.label', 'home')
    contact_collections.first.locator(':scope > .collection-siblings > button.add-collection').click()
    assert number_collections.count() == 2
    page.fill('#id_0\\.numbers\\.1\\.number\\.phone_number', "+1300400500")
    page.select_option('#id_0\\.numbers\\.1\\.number\\.label', 'mobile')
    contact_collections.first.locator(':scope > .collection-siblings > button.add-collection').click()
    assert number_collections.count() == 3
    page.fill('#id_0\\.numbers\\.2\\.number\\.phone_number', "+1400500600")
    page.select_option('#id_0\\.numbers\\.2\\.number\\.label', 'work')
    drag_handle = 'django-formset > .collection-siblings > django-form-collection > .collection-siblings > django-form-collection[sibling-position="2"] > .collection-drag-handle'
    pos_x, pos_y = page.locator(drag_handle).evaluate('elem => { const after = window.getComputedStyle(elem, "::after"); return [after.left, after.top]; }')
    position = {'x': int(pos_x.rstrip('px')), 'y': int(pos_y.rstrip('px'))}
    page.drag_and_drop(
        drag_handle,
        'django-formset > .collection-siblings > django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"]',
        source_position=position,
        target_position=position,
    )

    assert contact_collections.count() == 1
    page.locator('django-formset > .collection-siblings > button.add-collection').click()
    assert contact_collections.count() == 2
    number_collections = contact_collections.last.locator(':scope > .collection-siblings > django-form-collection')
    assert number_collections.count() == 1
    page.fill('#id_1\\.person\\.full_name', "James Last")
    page.fill('#id_1\\.person\\.email', "james@example.com")
    page.fill('#id_1\\.numbers\\.0\\.number\\.phone_number', "+441234567890")
    page.select_option('#id_1\\.numbers\\.0\\.number\\.label', 'work')
    contact_collections.last.locator(':scope > .collection-siblings > button.add-collection').click()
    assert number_collections.count() == 2
    page.fill('#id_1\\.numbers\\.1\\.number\\.phone_number', "+441222333444")
    page.select_option('#id_1\\.numbers\\.1\\.number\\.label', 'mobile')

    drag_handle = 'django-formset > .collection-siblings > django-form-collection[sibling-position="0"] > .collection-drag-handle'
    page.drag_and_drop(
        drag_handle,
        'django-formset > .collection-siblings > django-form-collection[sibling-position="1"]',
        source_position=position,
        target_position=position,
    )

    spy = mocker.spy(FormCollectionView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {
        'formset_data': [{
            'person': {'full_name': 'James Last', 'email': 'james@example.com'},
            'numbers': [
                {'number': {'phone_number': '+441234567890', 'label': 'work'}},
                {'number': {'phone_number': '+441222333444', 'label': 'mobile'}},
            ],
        }, {
            'person': {'full_name': 'Margret First', 'email': 'margret@example.com'},
            'numbers': [
                {'number': {'phone_number': '+1400500600', 'label': 'work'}},
                {'number': {'phone_number': '+1200300400', 'label': 'home'}},
                {'number': {'phone_number': '+1300400500', 'label': 'mobile'}},
            ],
        }],
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['sortedcontact'])
def test_submit_resetted_collection(page, mocker, viewname):
    contact_collections = page.locator('django-formset > django-form-collection:last-of-type')
    number_collections = contact_collections.first.locator(':scope > .collection-siblings > django-form-collection')
    assert number_collections.count() == 5
    drag_handle = 'django-formset > django-form-collection:last-of-type > .collection-siblings > django-form-collection[sibling-position="0"] > .collection-drag-handle'
    pos_x, pos_y = page.locator(drag_handle).evaluate('elem => { const after = window.getComputedStyle(elem, "::after"); return [after.left, after.top]; }')
    position = {'x': int(pos_x.rstrip('px')), 'y': int(pos_y.rstrip('px'))}
    page.drag_and_drop(
        drag_handle,
        'django-formset > django-form-collection:last-of-type > .collection-siblings > django-form-collection[sibling-position="4"]',
        source_position=position,
        target_position=position,
    )
    drag_handle = 'django-formset > django-form-collection:last-of-type > .collection-siblings > django-form-collection[sibling-position="2"] > .collection-drag-handle'
    page.drag_and_drop(
        drag_handle,
        'django-formset > django-form-collection:last-of-type > .collection-siblings > django-form-collection[sibling-position="0"]',
        source_position=position,
        target_position=position,
    )
    sleep(0.1)

    spy = mocker.spy(FormCollectionView, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {
        'formset_data': {
            'person': {'full_name': '', 'email': ''},
            'numbers': [
                {'number': {'phone_number': '+41 91 667914', 'label': 'home'}},
                {'number': {'phone_number': '+33 1 43478293', 'label': 'home'}},
                {'number': {'phone_number': '+39 335 327041', 'label': 'home'}},
                {'number': {'phone_number': '+49 89 7178864', 'label': 'home'}},
                {'number': {'phone_number': '+1 234 567 8900', 'label': 'home'}},
            ],
        }
    }

    page.wait_for_selector('django-formset').evaluate('elem => elem.reset()')
    page.fill('#id_person\\.full_name', "Margret First")
    page.fill('#id_person\\.email', "margret@example.com")
    page.wait_for_selector('#id_person\\.email').evaluate('elem => elem.blur()')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {
        'formset_data': {
            'person': {'full_name': 'Margret First', 'email': 'margret@example.com'},
            'numbers': [
                {'number': {'phone_number': '+1 234 567 8900', 'label': 'home'}},
                {'number': {'phone_number': '+33 1 43478293', 'label': 'home'}},
                {'number': {'phone_number': '+39 335 327041', 'label': 'home'}},
                {'number': {'phone_number': '+41 91 667914', 'label': 'home'}},
                {'number': {'phone_number': '+49 89 7178864', 'label': 'home'}},
            ],
        }
    }
