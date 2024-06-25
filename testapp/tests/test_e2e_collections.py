import json
import pytest
from playwright.sync_api import expect
from time import sleep

from django.forms import fields, forms
from django.urls import path

from formset.collection import FormCollection
from formset.utils import MARKED_FOR_REMOVAL
from formset.views import FormCollectionView

from .utils import ContextMixin, get_javascript_catalog


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
    label = fields.ChoiceField(
        label="Label",
        choices=[
            ('home', "Home"),
            ('work', "Work"),
            ('mobile', "Mobile"),
            ('other', "Other"),
        ],
    )


class PhoneNumberCollection(FormCollection):
    legend = "List of Phone Numbers"
    add_label = "Add new Phone Number"
    min_siblings = 1
    max_siblings = 5
    extra_siblings = 1
    number = PhoneNumberForm()


class ContactCollection(FormCollection):
    person = PersonForm()
    numbers = PhoneNumberCollection()


class SortedContactCollection(ContactCollection):
    numbers = PhoneNumberCollection(
        is_sortable=True,
    )


class BulkContactCollections(FormCollection):
    min_siblings = 0
    max_siblings = 3
    extra_siblings = 1
    add_label = "Add new Contact"

    person = PersonForm()

    numbers = PhoneNumberCollection(
        min_siblings=1,
        max_siblings=5,
        extra_siblings=1,
    )


initial_sample_data = {
    'person': {
        'full_name': "John Doe",
        'email': "john@example.com",
    },
    'numbers': [
        {'number': {'phone_number': "+1 234 567 8900"}},
        {'number': {'phone_number': "+33 1 43478293"}},
        {'number': {'phone_number': "+39 335 327041"}},
        {'number': {'phone_number': "+41 91 667914"}},
        {'number': {'phone_number': "+49 89 7178864"}},
    ],
}


initial_bulk_sample_data = [{
    'person': {
        'full_name': "John Doe",
        'email': "john@example.com",
    },
    'numbers': [
        {'number': {'phone_number': "+1 234 567 8900"}},
        {'number': {'phone_number': "+33 1 43478293"}},
    ],
}, {
    'person': {
        'full_name': "Johanna Doe",
        'email': "johanna@example.com",
    },
    'numbers': [
        {'number': {'phone_number': "+39 335 327041"}},
        {'number': {'phone_number': "+41 91 667914"}},
        {'number': {'phone_number': "+49 89 7178864"}},
    ],
}]


class FormCollectionView(ContextMixin, FormCollectionView):
    success_url='/success'


urlpatterns = [
    path('contact', FormCollectionView.as_view(
        collection_class=ContactCollection,
        template_name='testapp/form-collection.html',
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='contact'),
    path('sorted_contact', FormCollectionView.as_view(
        collection_class=SortedContactCollection,
        template_name='testapp/form-collection.html',
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='sorted_contact'),
    path('initial_contact', FormCollectionView.as_view(
        collection_class=ContactCollection,
        template_name='testapp/form-collection.html',
        initial=initial_sample_data,
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='initial_contact'),
    path('sorted_initial_contact', FormCollectionView.as_view(
        collection_class=SortedContactCollection,
        template_name='testapp/form-collection.html',
        initial=initial_sample_data,
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='sorted_initial_contact'),
    path('bulk_contacts', FormCollectionView.as_view(
        collection_class=BulkContactCollections,
        template_name='testapp/form-collection.html',
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='bulk_contacts'),
    path('bulk_initial_contacts', FormCollectionView.as_view(
        collection_class=BulkContactCollections,
        template_name='testapp/form-collection.html',
        initial=initial_bulk_sample_data,
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='bulk_initial_contacts'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contact', 'sorted_contact', 'initial_contact', 'sorted_initial_contact'])
def test_submit_collection(page, mocker, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    expect(form_collection.first.locator('> .collection-siblings')).to_have_count(0)
    expect(form_collection.last.locator('> .collection-siblings')).to_have_count(1)
    page.fill('#id_person\\.full_name', "John Doe")
    page.fill('#id_person\\.email', "john@example.com")
    page.fill('#id_numbers\\.0\\.number\\.phone_number', "+1200300400")
    page.select_option('#id_numbers\\.0\\.number\\.label', 'work')
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    expected = {'formset_data': {
        'person': {'full_name': 'John Doe', 'email': 'john@example.com'},
        'numbers': [{'number': {'phone_number': '+1200300400', 'label': 'work'}}],
    }}
    if viewname in ['initial_contact', 'sorted_initial_contact']:
        expected['formset_data']['numbers'].extend([
            {'number': {'phone_number': "+33 1 43478293", 'label': 'home'}},
            {'number': {'phone_number': "+39 335 327041", 'label': 'home'}},
            {'number': {'phone_number': "+41 91 667914", 'label': 'home'}},
            {'number': {'phone_number': "+49 89 7178864", 'label': 'home'}},
        ])
    assert request_body == expected
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contact', 'sorted_contact'])
def test_add_and_remove_collections(page, mocker, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    expect(form_collection.first.locator('> .collection-siblings')).to_have_count(0)
    expect(form_collection.last.locator('> .collection-siblings')).to_have_count(1)
    numbers_collection = form_collection.last.locator('> .collection-siblings')
    add_collection = numbers_collection.locator('> .add-collection')
    for _ in range(4):
        expect(add_collection).not_to_be_disabled()
        add_collection.click()
    expect(add_collection).to_be_disabled()
    expect(numbers_collection.locator('> django-form-collection')).to_have_count(5)
    for pos in range(5):
        expect(numbers_collection.locator(f'> django-form-collection[sibling-position="{pos}"] > .remove-collection')).not_to_be_disabled()
    numbers_collection.locator('> django-form-collection[sibling-position="4"]').hover()
    numbers_collection.locator('> django-form-collection[sibling-position="4"] > .remove-collection').click()
    expect(add_collection).not_to_be_disabled()
    expect(numbers_collection.locator('> django-form-collection')).to_have_count(4)
    numbers_collection.locator('> django-form-collection[sibling-position="0"]').hover()
    numbers_collection.locator('> django-form-collection[sibling-position="0"] > .remove-collection').click()
    expect(numbers_collection.locator('> django-form-collection')).to_have_count(4)
    expect(numbers_collection.locator('> django-form-collection[sibling-position="0"]')).to_have_class('dj-marked-for-removal')
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {'formset_data': {
        'person': {'full_name': '', 'email': ''},
        'numbers': [
            {'number': {'phone_number': '', 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': '', 'label': 'home'}},
        ],
    }}
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 422
    response = json.loads(spy.spy_return.content)
    is_required = ['This field is required.']
    assert response == {
        'person': {'full_name': is_required, 'email': is_required},
        'numbers': [
            {'number': {}},
            {'number': {'phone_number': is_required}},
        ],
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['initial_contact', 'sorted_initial_contact'])
def test_remove_and_add_collections(page, mocker, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    expect(form_collection.first.locator('> .collection-siblings')).to_have_count(0)
    expect(form_collection.last.locator('> .collection-siblings > django-form-collection')).to_have_count(5)
    numbers_collection = form_collection.last.locator('> .collection-siblings')
    add_collection = numbers_collection.locator('> .add-collection')
    expect(add_collection).to_be_disabled()
    for position in range(4):
        collection_sibling = numbers_collection.locator(f'django-form-collection[sibling-position="{position}"]')
        collection_sibling.hover()
        expect(collection_sibling.locator('> .remove-collection')).not_to_be_disabled()
        collection_sibling.locator('> .remove-collection').click()
    collection_sibling = numbers_collection.locator('django-form-collection[sibling-position="4"]')
    collection_sibling.hover()
    expect(collection_sibling.locator('> .remove-collection')).to_be_disabled()
    expect(add_collection).not_to_be_disabled()
    add_collection.click()
    page.fill('#id_numbers\\.5\\.number\\.phone_number', "+1200300400")
    page.select_option('#id_numbers\\.5\\.number\\.label', 'work')
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {'formset_data': {
        'person': {'full_name': 'John Doe', 'email': 'john@example.com'},
        'numbers': [
            {'number': {'phone_number': '+1 234 567 8900', 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': '+33 1 43478293', 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': '+39 335 327041', 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': '+41 91 667914', 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': '+49 89 7178864', 'label': 'home'}},
            {'number': {'phone_number': '+1200300400', 'label': 'work'}},
        ],
    }}
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contact', 'sorted_contact'])
def test_reset_and_submit_collections(page, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    expect(form_collection.first.locator('> .collection-siblings')).to_have_count(0)
    expect(form_collection.last.locator('> .collection-siblings')).to_have_count(1)
    numbers_collection = form_collection.last.locator('> .collection-siblings')
    add_collection = numbers_collection.locator('> .add-collection')
    page.fill('#id_person\\.full_name', "Mona Lisa")
    page.fill('#id_person\\.email', "mona@example.com")
    for position in range(5):
        page.fill(f'#id_numbers\\.{position}\\.number\\.phone_number', "+1200300400")
        page.select_option(f'#id_numbers\\.{position}\\.number\\.label', 'work')
        if position < 4:
            add_collection.click()
    page.locator('django-formset').evaluate('elem => elem.reset()')
    expect(page.locator('#id_person\\.full_name')).to_be_empty()
    expect(page.locator('#id_person\\.email')).to_be_empty()
    expect(page.locator('#id_numbers\\.0\\.number\\.phone_number')).to_be_empty()
    expect(page.locator('#id_numbers\\.0\\.number\\.label')).to_have_value('home')
    expect(numbers_collection.locator('django-form-collection')).to_have_count(1)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['initial_contact', 'sorted_initial_contact'])
def test_reset_initialized_collections(page, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    expect(form_collection.first.locator('> .collection-siblings')).to_have_count(0)
    expect(form_collection.last.locator('> .collection-siblings')).to_have_count(1)
    numbers_collection = form_collection.last.locator('> .collection-siblings')
    expect(numbers_collection.locator('django-form-collection')).to_have_count(5)
    for position in range(1, 5):
        collection_sibling = numbers_collection.locator(f'django-form-collection[sibling-position="{position}"]')
        collection_sibling.hover()
        expect(collection_sibling.locator('> .remove-collection')).not_to_be_disabled()
        collection_sibling.locator('> .remove-collection').click()
    page.fill('#id_person\\.full_name', "Mona Lisa")
    page.fill('#id_person\\.email', "mona@example.com")
    page.fill('#id_numbers\\.0\\.number\\.phone_number', "+1200300400")
    page.select_option('#id_numbers\\.0\\.number\\.label', 'work')
    page.locator('django-formset').evaluate('elem => elem.reset()')
    expect(page.locator('#id_person\\.full_name')).to_have_value("John Doe")
    expect(page.locator('#id_person\\.email')).to_have_value("john@example.com")
    for position in range(5):
        phone_number = initial_sample_data['numbers'][position]['number']['phone_number']
        expect(page.locator(f'#id_numbers\\.{position}\\.number\\.phone_number')).to_have_value(phone_number)
        expect(page.locator(f'#id_numbers\\.{position}\\.number\\.label')).to_have_value('home')
        expect(numbers_collection.locator(f'django-form-collection[sibling-position="{position}"]')).not_to_have_class('dj-marked-for-removal')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['sorted_initial_contact'])
def test_submit_sorted_initialized_collections(page, mocker, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    expect(form_collection.first.locator('> .collection-siblings')).to_have_count(0)
    expect(form_collection.last.locator('> .collection-siblings')).to_have_count(1)
    numbers_collection = form_collection.last.locator('> .collection-siblings')
    expect(numbers_collection.locator('django-form-collection')).to_have_count(5)
    drag_handle = numbers_collection.locator('django-form-collection[sibling-position="0"] > .collection-drag-handle')
    expect(drag_handle).to_be_visible()
    drag_handle.drag_to(numbers_collection.locator('django-form-collection[sibling-position="2"]'))
    drag_handle = numbers_collection.locator('django-form-collection[sibling-position="4"] > .collection-drag-handle')
    drag_handle.drag_to(numbers_collection.locator('django-form-collection[sibling-position="0"]'))
    drag_handle = numbers_collection.locator('django-form-collection[sibling-position="1"] > .collection-drag-handle')
    drag_handle.drag_to(numbers_collection.locator('django-form-collection[sibling-position="4"]'))
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {'formset_data': {
        'person': {'full_name': 'John Doe', 'email': 'john@example.com'},
        'numbers': [
            {'number': {'phone_number': "+49 89 7178864", 'label': 'home'}},
            {'number': {'phone_number': "+39 335 327041", 'label': 'home'}},
            {'number': {'phone_number': "+1 234 567 8900", 'label': 'home'}},
            {'number': {'phone_number': "+41 91 667914", 'label': 'home'}},
            {'number': {'phone_number': "+33 1 43478293", 'label': 'home'}},
        ],
    }}
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['sorted_initial_contact'])
def test_reset_sorted_initialized_collections(page, mocker, viewname):
    form_collection = page.locator('django-formset > django-form-collection')
    expect(form_collection.first.locator('> .collection-siblings')).to_have_count(0)
    expect(form_collection.last.locator('> .collection-siblings')).to_have_count(1)
    numbers_collection = form_collection.last.locator('> .collection-siblings')
    expect(numbers_collection.locator('django-form-collection')).to_have_count(5)
    drag_handle = numbers_collection.locator('django-form-collection[sibling-position="0"] > .collection-drag-handle')
    expect(drag_handle).to_be_visible()
    drag_handle.drag_to(numbers_collection.locator('django-form-collection[sibling-position="2"]'))
    drag_handle = numbers_collection.locator('django-form-collection[sibling-position="4"] > .collection-drag-handle')
    drag_handle.drag_to(numbers_collection.locator('django-form-collection[sibling-position="0"]'))
    drag_handle = numbers_collection.locator('django-form-collection[sibling-position="1"] > .collection-drag-handle')
    drag_handle.drag_to(numbers_collection.locator('django-form-collection[sibling-position="4"]'))
    page.locator('django-formset').evaluate('elem => elem.reset()')
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {'formset_data': {
        'person': {'full_name': 'John Doe', 'email': 'john@example.com'},
        'numbers': [
            {'number': {'phone_number': "+1 234 567 8900", 'label': 'home'}},
            {'number': {'phone_number': "+33 1 43478293", 'label': 'home'}},
            {'number': {'phone_number': "+39 335 327041", 'label': 'home'}},
            {'number': {'phone_number': "+41 91 667914", 'label': 'home'}},
            {'number': {'phone_number': "+49 89 7178864", 'label': 'home'}},
        ],
    }}
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['bulk_contacts'])
def test_submit_bulk(page, mocker, viewname):
    collection_siblings = page.locator('django-formset > .collection-siblings')
    expect(collection_siblings.locator('> django-form-collection')).to_have_count(1)
    page.fill('#id_0\\.person\\.full_name', "John Doe")
    page.fill('#id_0\\.person\\.email', "john@example.com")
    page.fill('#id_0\\.numbers\\.0\\.number\\.phone_number', "+1 200 300 400")
    page.select_option('#id_0\\.numbers\\.0\\.number\\.label', 'work')
    collection_siblings.locator('> .add-collection').click()
    expect(collection_siblings.locator('> django-form-collection')).to_have_count(2)
    page.fill('#id_1\\.person\\.full_name', "Johanna Doe")
    page.fill('#id_1\\.person\\.email', "johanna@example.com")
    page.fill('#id_1\\.numbers\\.0\\.number\\.phone_number', "+33 1 43478293")
    page.select_option('#id_1\\.numbers\\.0\\.number\\.label', 'work')
    collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > .add-collection').click()
    page.fill('#id_1\\.numbers\\.1\\.number\\.phone_number', "+39 335 327041")
    page.select_option('#id_1\\.numbers\\.1\\.number\\.label', 'work')
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    expected = {'formset_data': [{
        'numbers': [{'number': {'phone_number': '+1 200 300 400', 'label': 'work'}}],
        'person': {'full_name': 'John Doe', 'email': 'john@example.com'}
    }, {
        'numbers': [{
            'number': {'phone_number': '+33 1 43478293', 'label': 'work'},
        }, {
            'number': {'phone_number': '+39 335 327041', 'label': 'work'},
        }],
        'person': {'full_name': 'Johanna Doe', 'email': 'johanna@example.com'}
    }]}
    assert request_body == expected
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['bulk_initial_contacts'])
def test_initialized_bulk_remove_all(page, mocker, viewname):
    collection_siblings = page.locator('django-formset > .collection-siblings')
    expect(collection_siblings.locator('> django-form-collection')).to_have_count(3)
    expect(page.locator('#id_0\\.person\\.full_name')).to_have_value("John Doe")
    expect(page.locator('#id_0\\.person\\.email')).to_have_value("john@example.com")
    expect(page.locator('#id_0\\.numbers\\.0\\.number\\.phone_number')).to_have_value("+1 234 567 8900")
    expect(page.locator('#id_0\\.numbers\\.1\\.number\\.phone_number')).to_have_value("+33 1 43478293")
    expect(page.locator('#id_1\\.person\\.full_name')).to_have_value("Johanna Doe")
    expect(page.locator('#id_1\\.person\\.email')).to_have_value("johanna@example.com")
    expect(page.locator('#id_1\\.numbers\\.0\\.number\\.phone_number')).to_have_value("+39 335 327041")
    expect(page.locator('#id_1\\.numbers\\.1\\.number\\.phone_number')).to_have_value("+41 91 667914")
    expect(page.locator('#id_1\\.numbers\\.2\\.number\\.phone_number')).to_have_value("+49 89 7178864")
    collection_siblings.locator('> django-form-collection[sibling-position="0"]').hover()
    collection_siblings.locator('> django-form-collection[sibling-position="0"] > .remove-collection').click()
    collection_siblings.locator('> django-form-collection[sibling-position="1"]').hover()
    collection_siblings.locator('> django-form-collection[sibling-position="1"] > .remove-collection').click()
    collection_siblings.locator('> django-form-collection[sibling-position="2"]').hover()
    collection_siblings.locator('> django-form-collection[sibling-position="2"] > .remove-collection').click()
    expect(collection_siblings.locator('> django-form-collection')).to_have_count(2)
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    expected = {'formset_data': [{
        'person': {
            'full_name': "John Doe",
            'email': "john@example.com",
            MARKED_FOR_REMOVAL: True,
        },
        'numbers': [
            {'number': {'phone_number': "+1 234 567 8900", 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': "+33 1 43478293", 'label': 'home', MARKED_FOR_REMOVAL: True}},
        ],
    }, {
        'person': {
            'full_name': "Johanna Doe",
            'email': "johanna@example.com",
            MARKED_FOR_REMOVAL: True,
        },
        'numbers': [
            {'number': {'phone_number': "+39 335 327041", 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': "+41 91 667914", 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': "+49 89 7178864", 'label': 'home', MARKED_FOR_REMOVAL: True}},
        ],
    }]}
    assert request_body == expected
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['bulk_initial_contacts'])
def test_initialized_bulk_remove_partial_outer(page, mocker, viewname):
    collection_siblings = page.locator('django-formset > .collection-siblings')
    expect(collection_siblings.locator('> django-form-collection')).to_have_count(3)
    expect(page.locator('#id_0\\.person\\.full_name')).to_have_value("John Doe")
    expect(page.locator('#id_0\\.person\\.email')).to_have_value("john@example.com")
    expect(page.locator('#id_0\\.numbers\\.0\\.number\\.phone_number')).to_have_value("+1 234 567 8900")
    expect(page.locator('#id_0\\.numbers\\.1\\.number\\.phone_number')).to_have_value("+33 1 43478293")
    expect(page.locator('#id_1\\.person\\.full_name')).to_have_value("Johanna Doe")
    expect(page.locator('#id_1\\.person\\.email')).to_have_value("johanna@example.com")
    expect(page.locator('#id_1\\.numbers\\.0\\.number\\.phone_number')).to_have_value("+39 335 327041")
    expect(page.locator('#id_1\\.numbers\\.1\\.number\\.phone_number')).to_have_value("+41 91 667914")
    expect(page.locator('#id_1\\.numbers\\.2\\.number\\.phone_number')).to_have_value("+49 89 7178864")
    collection_siblings.locator('> django-form-collection[sibling-position="0"]').hover()
    collection_siblings.locator('> django-form-collection[sibling-position="0"] > .remove-collection').click()
    expect(collection_siblings.locator('> django-form-collection')).to_have_count(3)
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    expected = {'formset_data': [{
        'person': {
            'full_name': "John Doe",
            'email': "john@example.com",
            MARKED_FOR_REMOVAL: True,
        },
        'numbers': [
            {'number': {'phone_number': "+1 234 567 8900", 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': "+33 1 43478293", 'label': 'home', MARKED_FOR_REMOVAL: True}},
        ],
    }, {
        'person': {
            'full_name': "Johanna Doe",
            'email': "johanna@example.com",
        },
        'numbers': [
            {'number': {'phone_number': "+39 335 327041", 'label': 'home'}},
            {'number': {'phone_number': "+41 91 667914", 'label': 'home'}},
            {'number': {'phone_number': "+49 89 7178864", 'label': 'home'}},
        ],
    }]}
    assert request_body == expected
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['bulk_initial_contacts'])
def test_initialized_bulk_remove_partial_inner(page, mocker, viewname):
    collection_siblings = page.locator('django-formset > .collection-siblings')
    expect(collection_siblings.locator('> django-form-collection')).to_have_count(3)
    expect(page.locator('#id_0\\.person\\.full_name')).to_have_value("John Doe")
    expect(page.locator('#id_0\\.person\\.email')).to_have_value("john@example.com")
    expect(page.locator('#id_0\\.numbers\\.0\\.number\\.phone_number')).to_have_value("+1 234 567 8900")
    expect(page.locator('#id_0\\.numbers\\.1\\.number\\.phone_number')).to_have_value("+33 1 43478293")
    expect(page.locator('#id_1\\.person\\.full_name')).to_have_value("Johanna Doe")
    expect(page.locator('#id_1\\.person\\.email')).to_have_value("johanna@example.com")
    expect(page.locator('#id_1\\.numbers\\.0\\.number\\.phone_number')).to_have_value("+39 335 327041")
    expect(page.locator('#id_1\\.numbers\\.1\\.number\\.phone_number')).to_have_value("+41 91 667914")
    expect(page.locator('#id_1\\.numbers\\.2\\.number\\.phone_number')).to_have_value("+49 89 7178864")
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="1"]')
    inner_collection.hover()
    inner_collection.locator('> .remove-collection').click()
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection[sibling-position="0"]')
    inner_collection.hover()
    inner_collection.locator('> .remove-collection').click()
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection[sibling-position="2"]')
    inner_collection.hover()
    inner_collection.locator('> .remove-collection').click()
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    expected = {'formset_data': [{
        'person': {
            'full_name': "John Doe",
            'email': "john@example.com",
        },
        'numbers': [
            {'number': {'phone_number': "+1 234 567 8900", 'label': 'home'}},
            {'number': {'phone_number': "+33 1 43478293", 'label': 'home', MARKED_FOR_REMOVAL: True}},
        ],
    }, {
        'person': {
            'full_name': "Johanna Doe",
            'email': "johanna@example.com",
        },
        'numbers': [
            {'number': {'phone_number': "+39 335 327041", 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': "+41 91 667914", 'label': 'home'}},
            {'number': {'phone_number': "+49 89 7178864", 'label': 'home', MARKED_FOR_REMOVAL: True}},
        ],
    }]}
    assert request_body == expected
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['bulk_initial_contacts'])
def test_initialized_bulk_remove_all_inner(page, mocker, viewname):
    collection_siblings = page.locator('django-formset > .collection-siblings')
    expect(collection_siblings.locator('> django-form-collection')).to_have_count(3)
    expect(page.locator('#id_0\\.person\\.full_name')).to_have_value("John Doe")
    expect(page.locator('#id_0\\.person\\.email')).to_have_value("john@example.com")
    expect(page.locator('#id_0\\.numbers\\.0\\.number\\.phone_number')).to_have_value("+1 234 567 8900")
    expect(page.locator('#id_0\\.numbers\\.1\\.number\\.phone_number')).to_have_value("+33 1 43478293")
    expect(page.locator('#id_1\\.person\\.full_name')).to_have_value("Johanna Doe")
    expect(page.locator('#id_1\\.person\\.email')).to_have_value("johanna@example.com")
    expect(page.locator('#id_1\\.numbers\\.0\\.number\\.phone_number')).to_have_value("+39 335 327041")
    expect(page.locator('#id_1\\.numbers\\.1\\.number\\.phone_number')).to_have_value("+41 91 667914")
    expect(page.locator('#id_1\\.numbers\\.2\\.number\\.phone_number')).to_have_value("+49 89 7178864")
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="0"]')
    inner_collection.hover()
    inner_collection.locator('> .remove-collection').click()
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="1"]')
    inner_collection.hover()
    inner_collection.locator('> .remove-collection').click()
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="0"] > .collection-siblings > django-form-collection[sibling-position="2"]')
    inner_collection.hover()
    expect(inner_collection.locator('> .remove-collection')).to_be_disabled()
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection[sibling-position="0"]')
    inner_collection.hover()
    inner_collection.locator('> .remove-collection').click()
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection[sibling-position="2"]')
    inner_collection.hover()
    inner_collection.locator('> .remove-collection').click()
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection[sibling-position="3"]')
    expect(collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection')).to_have_count(4)
    inner_collection.hover()
    inner_collection.locator('> .remove-collection').click()
    expect(collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection')).to_have_count(3)
    inner_collection = collection_siblings.locator('> django-form-collection[sibling-position="1"] > .collection-siblings > django-form-collection[sibling-position="1"]')
    inner_collection.hover()
    expect(inner_collection.locator('> .remove-collection')).to_be_disabled()
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    expected = {'formset_data': [{
        'person': {
            'full_name': "John Doe",
            'email': "john@example.com",
        },
        'numbers': [
            {'number': {'phone_number': "+1 234 567 8900", 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': "+33 1 43478293", 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': '', 'label': 'home'}},
        ],
    }, {
        'person': {
            'full_name': "Johanna Doe",
            'email': "johanna@example.com",
        },
        'numbers': [
            {'number': {'phone_number': "+39 335 327041", 'label': 'home', MARKED_FOR_REMOVAL: True}},
            {'number': {'phone_number': "+41 91 667914", 'label': 'home'}},
            {'number': {'phone_number': "+49 89 7178864", 'label': 'home', MARKED_FOR_REMOVAL: True}},
        ],
    }]}
    assert request_body == expected
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 422
    response = json.loads(spy.spy_return.content)
    assert response[0]['numbers'][2]['number']['phone_number'] == ["This field is required."]
