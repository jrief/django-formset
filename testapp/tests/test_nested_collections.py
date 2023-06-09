import json

import bs4
import pytest
from bs4 import BeautifulSoup, Tag

from django.test import Client, RequestFactory
from django.utils.timezone import datetime
from django.views.generic.edit import CreateView, UpdateView

from formset.views import EditCollectionView, BulkEditCollectionView

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
    Department.objects.create(name="Finance", company=company)
    return company

@pytest.mark.django_db
def test_edit_company_department(single_collection_view, created_company):
    form_data = {
        'formset_data': {
            'departments': [{
                "teams": [],
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


@pytest.mark.django_db
def test_edit_company_add_department(single_collection_view, created_company):
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
def test_edit_company_ununique_department(single_collection_view, created_company):
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
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
    company = Company.objects.last()
    assert company.name == "Pepsi"
    assert company.departments.order_by('id').first().name == "Finance"
    assert company.departments.order_by('id').last().name == "Marketing"
