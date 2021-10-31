import pytest

import json
from bs4 import BeautifulSoup
from copy import copy
from django.test import RequestFactory
from formset.views import FormView, FormCollectionView

from .forms.contact import SimpleContactCollection, PersonForm, sample_person_data


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
