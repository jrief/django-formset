import pytest

import json
from bs4 import BeautifulSoup
from copy import copy
from django.test import RequestFactory
from formset.views import FormView, FormCollectionView

from .forms.contact import SimpleContactCollection, PersonForm, sample_person_data, ContactCollection


def test_person_form_get():
    view = FormView.as_view(
        form_class=PersonForm,
        template_name='bootstrap/form-fields.html',
    )
    response = view(RequestFactory().get('/'))
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    form_elem = soup.find('form')
    assert form_elem is not None
    assert 'row' in form_elem.attrs['class']
    field_group_elems = form_elem.find_all('django-field-group')
    assert len(field_group_elems) == 4
    assert all(map(lambda elem: 'mb-2' in elem.attrs['class'], field_group_elems))
    assert 'col-12' in field_group_elems[0].attrs['class']
    assert 'col-12' in field_group_elems[1].attrs['class']
    assert 'col-8' in field_group_elems[2].attrs['class']
    assert 'col-4' in field_group_elems[3].attrs['class']


def test_person_form_post():
    view = FormView.as_view(
        form_class=PersonForm,
        template_name='bootstrap/form-fields.html',
    )
    formset_data = copy(sample_person_data)
    http_request = RequestFactory().post('/', data={'formset_data': formset_data}, content_type='application/json')
    response = view(http_request)
    assert response.status_code == 422
    body = json.loads(response.content)
    assert body['email_label'] == ["This field is required."]

    # fix the missing field
    formset_data['email_label'] = 'home'
    http_request = RequestFactory().post('/', data={'formset_data': formset_data}, content_type='application/json')
    response = view(http_request)
    assert response.status_code == 200
    body = json.loads(response.content)
    assert body == {}  # no success URL given


@pytest.mark.parametrize('initial', [{}, {'person': sample_person_data}])
def test_simple_collection_get(initial):
    view = FormCollectionView.as_view(
        collection_class=SimpleContactCollection,
        template_name='bootstrap/form-collection.html',
        initial=initial,
    )
    response = view(RequestFactory().get('/'))
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    collection_elems = soup.find_all('django-form-collection')
    assert len(collection_elems) == 2

    form_elem = collection_elems[0].find('form')
    assert form_elem is not None
    assert form_elem.attrs['name'] == 'person'
    assert form_elem.attrs['id'] == 'id_person'
    field_group_elems = form_elem.find_all('django-field-group')
    assert len(field_group_elems) == 4
    input_elems = form_elem.find_all('input')
    assert len(input_elems) == 3
    for input_elem in input_elems:
        name = input_elem.attrs['name']
        assert input_elem.attrs['form'] == 'id_person'
        assert input_elem.attrs['id'] == f'id_person.{name}'
        if initial:
            assert input_elem.attrs['value'] == initial['person'][name]
        else:
            assert 'value' not in input_elem.attrs

    form_elem = collection_elems[1].find('form')
    assert form_elem.attrs['name'] == 'profession'
    assert form_elem.attrs['id'] == 'id_profession'
    field_group_elems = form_elem.find_all('django-field-group')
    assert len(field_group_elems) == 2
    input_elems = form_elem.find_all('input')
    assert len(input_elems) == 2
    for input_elem in input_elems:
        name = input_elem.attrs['name']
        assert input_elem.attrs['form'] == 'id_profession'
        assert input_elem.attrs['id'] == f'id_profession.{name}'
        assert 'value' not in input_elem.attrs  # profession has no initial data


def test_simple_collection_post():
    view = FormCollectionView.as_view(
        collection_class=SimpleContactCollection,
        success_url='/success',
        template_name='bootstrap/form-collection.html',
    )
    formset_data = {
        'person': copy(sample_person_data),
        'profession': {
            'company': "django-formset",
        }
    }
    http_request = RequestFactory().post('/', data={'formset_data': formset_data}, content_type='application/json')
    response = view(http_request)
    assert response.status_code == 422
    body = json.loads(response.content)
    assert body['person']['email_label'] == ["This field is required."]

    # fix the missing field
    formset_data['person']['email_label'] = 'home'
    http_request = RequestFactory().post('/', data={'formset_data': formset_data}, content_type='application/json')
    response = view(http_request)
    assert response.status_code == 200
    body = json.loads(response.content)
    assert body == {'success_url': '/success'}


def test_collection_get():
    view = FormCollectionView.as_view(
        collection_class=ContactCollection,
        template_name='bootstrap/form-collection.html',
        initial={'person': sample_person_data},
    )
    response = view(RequestFactory().get('/'))
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    formset_elem = soup.find('django-formset')
    assert formset_elem is not None

    collection_elems = formset_elem.find_all('django-form-collection', recursive=False)
    assert len(collection_elems) == 2
    form_elem = collection_elems[0].find('form')
    assert form_elem is not None
    assert form_elem.attrs['name'] == 'person'
    assert collection_elems[0].find('django-form-collection') is None

    collection_sibling_elems = collection_elems[1].find_all('django-form-collection', recursive=False)
    assert len(collection_sibling_elems) == 2
    for counter, collection_sibling_elem in enumerate(collection_sibling_elems):
        assert collection_sibling_elem.attrs['sibling-position'] == str(counter)
        assert collection_sibling_elem.attrs['min-siblings'] == '2'
        form_elem = collection_sibling_elem.find('form')
        assert form_elem.attrs['name'] == f'numbers.{counter}.number'
        assert form_elem.attrs['id'] == f'id_numbers.{counter}.number'
        button_elem = form_elem.find_next_sibling('button', class_='remove-collection')
        assert button_elem is not None
    template_elem = collection_sibling_elems[1].find_next_sibling('template', class_='empty-collection')
    assert template_elem is not None
    empty_collection_sibling = template_elem.find('django-form-collection')
    empty_collection_sibling is not None
    assert empty_collection_sibling.attrs['sibling-position'] == '${position}'
    assert empty_collection_sibling.attrs['min-siblings'] == '2'
    form_elem = empty_collection_sibling.find('form')
    assert form_elem.attrs['name'] == 'numbers.${position}.number'
    assert form_elem.attrs['id'] == 'id_numbers.${position}.number'
    button_elem = form_elem.find_next_sibling('button', class_='remove-collection')
    assert button_elem is not None
    input_elem = empty_collection_sibling.find('input')
    assert input_elem is not None
    assert input_elem.attrs['name'] == 'phone_number'
    assert input_elem.attrs['form'] == 'id_numbers.${position}.number'
    assert input_elem.attrs['id'] == 'id_numbers.${position}.number.phone_number'
    button_elem = template_elem.find_next_sibling('button', class_='add-collection')
    assert button_elem is not None

collection_formset_data = [{
    'person': dict(sample_person_data, email_label='home'),
    'numbers': [{
        'number': {
            'phone_number': '+18007006000',
            'label': 'work',
        }
    }],
}, {
    'person': dict(sample_person_data, email_label='home'),
    'numbers': 7 * [{
        'number': {
            'phone_number': '+18007006000',
            'label': 'work',
        }
    }],
}, {
    'person': dict(sample_person_data, email_label='home'),
    'numbers': [{
        'number': {
            'phone_number': '+18007006000',
            'label': 'work',
        }
    }, {
        'number': {
            'phone_number': '+123456789',
            'label': 'work',
        }
    }],
}, {
    'person': dict(sample_person_data, email_label='home'),
    'numbers': [{
        'number': {
            'phone_number': '+18007006000',
        }
    }, {
        'number': {
            'phone_number': '+1200300400',
            'label': 'work',
        }
    }],
}, {
    'person': dict(sample_person_data, email_label='home'),
    'numbers': [{
        'number': {
            'phone_number': '+1800700600',
            'label': 'home',
        }
    }, {
        'number': {
            'phone_number': '+120x300400',
            'label': 'work',
        }
    }],
}, {
    'person': dict(sample_person_data, email_label='home'),
    'numbers': [{
        'number': {
            'phone_number': '+18007006000',
            'label': 'home',
        }
    }, {
        'number': {
            'phone_number': '+1200300400',
            'label': 'work',
        }
    }],
}]


@pytest.mark.parametrize('counter,formset_data', enumerate(collection_formset_data))
def test_collection_post(counter, formset_data):
    view = FormCollectionView.as_view(
        collection_class=ContactCollection,
        success_url='/success',
        template_name='bootstrap/form-collection.html',
    )
    http_request = RequestFactory().post('/', data={'formset_data': formset_data}, content_type='application/json')
    response = view(http_request)
    body = json.loads(response.content)
    if counter == 0:
        assert response.status_code == 422
        assert body['numbers'][0]['__all__'] == ["Too few siblings."]
    if counter == 1:
        assert response.status_code == 422
        assert body['numbers'][0]['__all__'] == ["Too many siblings."]
    if counter == 2:
        assert response.status_code == 422
        assert body['numbers'][1]['number']['phone_number'] == ["Are you kidding me?"]
    if counter == 3:
        assert response.status_code == 422
        assert body['numbers'][0]['number']['label'] == ["This field is required."]
    if counter == 4:
        assert response.status_code == 422
        assert body['numbers'][1]['number']['phone_number'] == ["Enter a valid value."]
    if counter == 5:
        assert response.status_code == 200
        assert body['success_url'] == '/success'
