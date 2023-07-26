import json

import pytest
from bs4 import BeautifulSoup, Tag

from django.core.exceptions import NON_FIELD_ERRORS
from django.forms import fields, forms
from django.test import RequestFactory

from formset.collection import COLLECTION_ERRORS, FormCollection
from formset.views import EditCollectionView, FormCollectionView

from testapp.forms.company import CompanyCollection
from testapp.models.company import Company, Department, Team


class CompanyCollectionView(EditCollectionView):
    model = Company
    collection_class = CompanyCollection
    success_url = '/success'
    template_name = 'testapp/form-collection.html'

    def get_object(self, queryset=None):
        return self.model(created_by='dummysessionid')


@pytest.fixture
def single_collection_view():
    return CompanyCollectionView.as_view()


def test_render(single_collection_view):
    request = RequestFactory().get('/')
    response = single_collection_view(request)
    response.render()
    soup = BeautifulSoup(response.content, 'html.parser')
    django_formset = soup.find('django-formset')
    assert isinstance(django_formset, Tag)
    input_field = django_formset.find(id='id_company')
    assert isinstance(input_field, Tag)


@pytest.mark.django_db
def test_create_company(single_collection_view):
    form_data = {
        "formset_data": {
            "departments": [],
            "company": {"name": "Pepsi"},
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = single_collection_view(request)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
    company = Company.objects.last()
    assert company.name == "Pepsi"


@pytest.mark.django_db
def test_create_company_with_department(single_collection_view):
    form_data = {
        'formset_data': {
            'departments': [{
                "teams": [],
                "department": {
                    "name": "Marketing",
                }
            }],
            "company": {"name": "Pepsi"},
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = single_collection_view(request)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
    company = Company.objects.last()
    assert company.name == "Pepsi"
    assert company.departments.first().name == "Marketing"


@pytest.fixture
def created_company():
    company = Company.objects.create(name="Pepsi")
    department = Department.objects.create(name="Finance", company=company)
    Team.objects.create(name="Accounting", department=department)
    return company

@pytest.mark.django_db
def test_edit_copmany_and_department_and_team(single_collection_view, created_company):
    form_data = {
        'formset_data': {
            'departments': [{
                "teams": [{
                    "team": {
                        "name": "Social Media",
                        "id": created_company.departments.first().teams.first().id,
                    }
                }],
                "department": {
                    "name": "Marketing",
                    "id": created_company.departments.first().id,
                }
            }],
            "company": {"name": "Coke"},
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = single_collection_view(request)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
    company = Company.objects.last()
    assert company.name == "Coke"
    assert company.departments.first().name == "Marketing"
    assert company.departments.first().teams.first().name == "Social Media"


@pytest.mark.django_db
def test_add_department(single_collection_view, created_company):
    department = created_company.departments.first()
    form_data = {
        'formset_data': {
            'departments': [{
                "teams": [],
                "department": {
                    "name": department.name,
                    "id": department.id,
                }
            }, {
                "teams": [],
                "department": {
                    "name": "Marketing",
                }
            }],
            "company": {"name": created_company.name},
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = single_collection_view(request)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
    company = Company.objects.last()
    assert company.name == "Pepsi"
    assert company.departments.order_by('id').first().name == "Finance"
    assert company.departments.order_by('id').last().name == "Marketing"


@pytest.mark.django_db
def test_check_unique_department(single_collection_view, created_company):
    department = created_company.departments.first()
    form_data = {
        'formset_data': {
            'departments': [{
                "teams": [],
                "department": {
                    "name": department.name,
                    "id": department.id,
                }
            }, {
                "teams": [],
                "department": {
                    "name": department.name,
                }
            }],
            "company": {"name": created_company.name},
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = single_collection_view(request)
    assert response.status_code == 422
    response_body = json.loads(response.getvalue())
    assert 'success_url' not in response_body
    expected = ['Please correct the duplicate data for name and company, which must be unique.']
    assert response_body['departments'][1]['department'][NON_FIELD_ERRORS] == expected


class PersonForm(forms.Form):
    full_name = fields.CharField(
        label="Full name",
        min_length=2,
        max_length=50,
    )


class PhoneNumberForm(forms.Form):
    phone_number = fields.RegexField(
        r'^[01+][ 0-9.\-]+$',
        label="Phone Number",
        min_length=2,
        max_length=20,
    )


class PhoneNumberCollection(FormCollection):
    min_siblings = 1
    max_siblings = 3
    extra_siblings = 1
    number = PhoneNumberForm()


class ContactCollection(FormCollection):
    person = PersonForm()
    numbers = PhoneNumberCollection()


@pytest.fixture
def contact_collection_view():
    return FormCollectionView.as_view(
        collection_class=ContactCollection,
    )


def test_check_too_many_collections(contact_collection_view):
    form_data = {
        'formset_data': {
            'person': {
                'full_name': "John Doe",
            },
            'numbers': [
                {'number': {'phone_number': "+1 234 567 8900"}},
                {'number': {'phone_number': "+33 1 43478293"}},
                {'number': {'phone_number': "+39 335 327041"}},
                {'number': {'phone_number': "+41 91 667914"}},
            ],
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = contact_collection_view(request)
    assert response.status_code == 422
    response_body = json.loads(response.getvalue())
    assert response_body == {
        'person': {},
        'numbers': [{COLLECTION_ERRORS: ['Too many entries in “PhoneNumberCollection”, please remove one.']}]
    }


def test_check_too_few_collections(contact_collection_view):
    form_data = {
        'formset_data': {
            'person': {
                'full_name': "John Doe",
            },
            'numbers': [],
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = contact_collection_view(request)
    assert response.status_code == 422
    response_body = json.loads(response.getvalue())
    assert response_body == {
        'person': {},
        'numbers': [{COLLECTION_ERRORS: ['Not enough entries in “PhoneNumberCollection”, please add another.']}]
    }


def test_missing_formset_data(contact_collection_view):
    form_data = {
        'person': {
            'full_name': "John Doe",
        },
        'numbers': [],
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = contact_collection_view(request)
    assert response.status_code == 422
    response_body = json.loads(response.getvalue())
    assert response_body == {
        'person': {NON_FIELD_ERRORS: ['Form data is missing.']},
        'numbers': {NON_FIELD_ERRORS: ['Form data is missing.']}
    }


def test_check_bogous_formset_data(contact_collection_view):
    form_data = {
        'formset_data': [0, 'A', 2]
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = contact_collection_view(request)
    assert response.status_code == 422
    response_body = json.loads(response.getvalue())
    assert response_body == {
        'person': {NON_FIELD_ERRORS: ['Form data is missing.']},
        'numbers': {NON_FIELD_ERRORS: ['Form data is missing.']}
    }


def test_check_boguous_collection_data(contact_collection_view):
    form_data = {
        'person': [0, 'A', 2],
        'numbers': {
            'full_name': "John Doe"
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = contact_collection_view(request)
    assert response.status_code == 422
    response_body = json.loads(response.getvalue())
    assert response_body == {
        'person': {NON_FIELD_ERRORS: ['Form data is missing.']},
        'numbers': {NON_FIELD_ERRORS: ['Form data is missing.']}
    }


def test_check_missing_collection_data(contact_collection_view):
    form_data = {
        'person': None,
        'numbers': None,
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = contact_collection_view(request)
    assert response.status_code == 422
    response_body = json.loads(response.getvalue())
    assert response_body == {
        'person': {NON_FIELD_ERRORS: ['Form data is missing.']},
        'numbers': {NON_FIELD_ERRORS: ['Form data is missing.']}
    }
