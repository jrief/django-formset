import json
import pytest
from playwright.sync_api import expect
from time import sleep

from django.forms import fields, forms
from django.urls import path

from formset.utils import MARKED_FOR_REMOVAL
from formset.collection import FormCollection
from formset.views import FormCollectionView


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


class ContactCollectionList(ContactCollection):
    min_siblings = 0
    max_siblings = 3
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
    #
    # path('sortedcontact', FormCollectionView.as_view(
    #     collection_class=ContactCollection,
    #     template_name='testapp/form-collection.html',
    #     extra_context={'force_submission': True},
    # ), name='sortedcontact'),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contact', 'sorted_contact', 'initial_contact', 'sorted_initial_contact'])
def test_submit(page, mocker, viewname):
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
def test_reset_collections(page, viewname):
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




@pytest.mark.skip
def test_submit_bulk(page, mocker, viewname):
    contact_collections = page.locator('django-formset > .collection-siblings > django-form-collection')
    expect(contact_collections).to_have_count(1)
    expect(contact_collections.locator('.collection-siblings > django-form-collection')).to_have_count(1)
    page.fill('#id_0\\.person\\.full_name', "John Doe")
    page.fill('#id_0\\.person\\.email', "john@example.com")
    page.fill('#id_0\\.numbers\\.0\\.number\\.phone_number', "+1200300400")
    page.select_option('#id_0\\.numbers\\.0\\.number\\.label', 'work')
    spy = mocker.spy(FormCollectionView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request_body = json.loads(spy.call_args.args[1].body)
    assert request_body == {'formset_data': [{
        'person': {'full_name': 'John Doe', 'email': 'john@example.com'},
        'numbers': [{'number': {'phone_number': '+1200300400', 'label': 'work'}}],
    }]}
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200


@pytest.mark.skip
@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contactlist', 'sortedcontactlist'])
def test_add_inner_collection(page, viewname):
    formset = page.locator('django-formset')
    inner_siblings = formset.locator('> .collection-siblings > django-form-collection > .collection-siblings')
    expect(inner_siblings.locator('> django-form-collection')).to_have_count(1)
    expect(inner_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection')).to_be_disabled()
    inner_siblings.locator('> button.add-collection').click()
    expect(inner_siblings.locator('> django-form-collection')).to_have_count(2)
    expect(inner_siblings.locator('> django-form-collection > button.remove-collection')).to_have_count(2)
    expect(inner_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection')).to_be_enabled()
    expect(inner_siblings.locator('> django-form-collection[sibling-position="1"] > button.remove-collection')).to_be_enabled()
    expect(inner_siblings.locator('> django-form-collection[sibling-position="1"]')).not_to_be_empty()
    inner_siblings.locator('> django-form-collection[sibling-position="1"] > button.remove-collection').click()
    expect(inner_siblings.locator('> django-form-collection[sibling-position="1"]')).to_have_count(0)
    inner_siblings.locator('> button.add-collection').click()
    expect(inner_siblings.locator('> django-form-collection[sibling-position="1"]')).not_to_be_empty()
    page.hover('django-form-collection > .collection-siblings > django-form-collection[sibling-position="0"]')
    inner_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection').click()
    expect(inner_siblings.locator('> django-form-collection[sibling-position="0"]')).to_have_class('dj-marked-for-removal')
    expect(inner_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection')).not_to_be_disabled()
    expect(inner_siblings.locator('> django-form-collection[sibling-position="1"] > button.remove-collection')).to_be_disabled()
    inner_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection').click()
    expect(inner_siblings.locator('> django-form-collection[sibling-position="0"]')).not_to_have_class('dj-marked-for-removal')
    expect(inner_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection')).not_to_be_disabled()
    expect(inner_siblings.locator('> django-form-collection[sibling-position="1"] > button.remove-collection')).not_to_be_disabled()


@pytest.mark.skip
@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['contactlist', 'sortedcontactlist'])
def test_add_outer_collection(page, viewname):
    outer_siblings = page.locator('django-formset > .collection-siblings')
    expect(outer_siblings.locator('> django-form-collection')).to_have_count(1)
    outer_siblings.locator('> button.add-collection').click()
    expect(outer_siblings.locator('> django-form-collection')).to_have_count(2)
    outer_siblings.locator('> button.add-collection').click()
    expect(outer_siblings.locator('> django-form-collection')).to_have_count(3)
    expect(outer_siblings.locator('> button.add-collection')).to_be_disabled()
    expect(outer_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection')).not_to_be_disabled()
    expect(outer_siblings.locator('> django-form-collection[sibling-position="1"] > button.remove-collection')).not_to_be_disabled()
    expect(outer_siblings.locator('> django-form-collection[sibling-position="2"] > button.remove-collection')).not_to_be_disabled()
    outer_siblings.locator('> django-form-collection[sibling-position="0"]').hover()
    outer_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection').click()
    expect(outer_siblings.locator('> django-form-collection')).to_have_count(2)
    expect(outer_siblings.locator('> django-form-collection[sibling-position="2"]')).to_have_count(0)
    outer_siblings.locator('> django-form-collection[sibling-position="1"]').hover()
    outer_siblings.locator('> django-form-collection[sibling-position="1"] > button.remove-collection').click()
    expect(outer_siblings.locator('> django-form-collection')).to_have_count(1)
    outer_siblings.locator('> django-form-collection[sibling-position="0"]').hover()
    outer_siblings.locator('> django-form-collection[sibling-position="0"] > button.remove-collection').click()
    expect(outer_siblings.locator('> django-form-collection')).to_have_count(0)


@pytest.mark.skip
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


@pytest.mark.skip
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


@pytest.mark.skip
@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['sortedcontact'])
def test_submit_resetted_collection(page, mocker, viewname):
    contact_collections = page.locator('django-formset > django-form-collection').last
    number_collections = contact_collections.first.locator(':scope > .collection-siblings > django-form-collection')
    assert number_collections.count() == 5
    drag_handle = contact_collections.locator('> .collection-siblings > django-form-collection[sibling-position="0"] > .collection-drag-handle')
    pos_x, pos_y = drag_handle.evaluate('elem => { const after = window.getComputedStyle(elem, "::after"); return [after.left, after.top]; }')
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
