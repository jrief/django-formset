import json

import bs4
import pytest
from bs4 import BeautifulSoup, Tag

from django.test import Client, RequestFactory
from django.utils.timezone import datetime
from django.views.generic.edit import CreateView, UpdateView

from formset.views import EditCollectionView, BulkEditCollectionView

from testapp.forms.company import CompanyCollection
from testapp.models import Company, Member, Team



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
        'formset_data': {
            'teams': [],
            'company': {'name': 'Pepsi'},
        }
    }
    request = RequestFactory().post('/', form_data, content_type='application/json')
    response = single_collection_view(request)
    assert response.status_code == 200
    assert json.loads(response.getvalue())['success_url'] == '/success'
    company = Company.objects.last()
    assert company.name == "Pepsi"
