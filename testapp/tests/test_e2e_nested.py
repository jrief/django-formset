import json
import pytest
from time import sleep
from playwright.sync_api import expect

from django.forms import fields, forms
from django.urls import path

from formset.collection import FormCollection
from formset.formfields.activator import Activator
from formset.utils import MARKED_FOR_REMOVAL
from formset.views import FormCollectionView
from formset.widgets import Button

from .utils import ContextMixin, get_javascript_catalog


class TeamForm(forms.Form):
    name = fields.CharField()


class TeamCollection(FormCollection):
    induce_add_sibling = '.add_team:active'
    min_siblings = 0
    extra_siblings = 1
    team = TeamForm()
    legend = "Teams"

    add_team = Activator(
        label="Add Team",
        widget=Button(
            action='activate("apply")',
            attrs={'omit-restore': True},
        )
    )


class DepartmentForm(forms.Form):
    name = fields.CharField()


class DepartmentCollection(FormCollection):
    legend = "Departments"
    induce_add_sibling = '.add_department:active'
    min_siblings = 0
    extra_siblings = 1
    department = DepartmentForm()
    teams = TeamCollection()

    add_department = Activator(
        label="Add Department",
        widget=Button(
            action='activate("apply")',
            attrs={'omit-restore': True},
        )
    )


class DepartmentCollectionMax(DepartmentCollection):
    min_siblings = 1
    max_siblings = 3
    extra_siblings = 1
    teams = TeamCollection(min_siblings=1, max_siblings=3)


class CompanyForm(forms.Form):
    name = fields.CharField()


class CompanyCollection0(FormCollection):
    company = CompanyForm()
    departments = DepartmentCollection()


class CompanyCollection1(FormCollection):
    company = CompanyForm()
    departments = DepartmentCollectionMax()


initial_sample_data = {
    'departments': [{
        'teams': [
            {'team': {'name': 'Atlanta'}}
        ],
        'department': {'name': 'Quality Assurance'}}
    ],
    'company': {'name': 'Coca Cola'},
}


class FormCollectionView(ContextMixin, FormCollectionView):
    success_url = '/success'


urlpatterns = [
    path('company_1', FormCollectionView.as_view(
        collection_class=CompanyCollection0,
        template_name='testapp/form-collection.html',
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='company_1'),
    path('company_2', FormCollectionView.as_view(
        collection_class=CompanyCollection0,
        template_name='testapp/form-collection.html',
        initial=initial_sample_data,
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='company_2'),
    path('company_3', FormCollectionView.as_view(
        collection_class=CompanyCollection1,
        template_name='testapp/form-collection.html',
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='company_3'),
    path('company_4', FormCollectionView.as_view(
        collection_class=CompanyCollection1,
        template_name='testapp/form-collection.html',
        initial=initial_sample_data,
        extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
    ), name='company_4'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['company_1', 'company_2'])
def test_fill_collection(page, mocker, viewname):
    formset = page.locator('django-formset')
    if viewname == 'company_1':
        expect(formset.locator('django-form-collection')).to_have_count(4)
    else:
        expect(formset.locator('django-form-collection')).to_have_count(7)
    page.fill('#id_company\\.name', "Pepsi")
    page.fill('#id_departments\\.0\\.department\\.name', "Marketing")
    page.fill('#id_departments\\.0\\.teams\\.0\\.team\\.name', "Canada")
    page.locator('#id_company\\.name').evaluate('elem => elem.focus()')
    spy = mocker.spy(FormCollectionView, 'post')
    formset.evaluate('elem => elem.submit()')
    sleep(0.2)
    body = json.loads(spy.call_args.args[1].body)
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    assert body == {
        'extra_data': {},
        'formset_data': {
            'departments': [{
                'teams': [
                    {'team': {'name': 'Canada'}}
                ],
                'department': {'name': 'Marketing'}
            }],
            'company': {'name': 'Pepsi'},
        },
    }


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['company_1', 'company_2'])
def test_partial_fill_collection(page, mocker, viewname):
    formset = page.locator('django-formset')
    if viewname == 'company_1':
        expect(formset.locator('django-form-collection')).to_have_count(4)
    else:
        expect(formset.locator('django-form-collection')).to_have_count(7)
        expect(page.locator('#id_departments\\.0\\.teams\\.1\\.team')).to_have_count(1)
        expect(page.locator('#id_departments\\.1\\.department')).to_have_count(1)
    page.fill('#id_company\\.name', "Pepsi")
    page.fill('#id_departments\\.0\\.department\\.name', "Marketing")
    if viewname == 'company_2':
        page.hover('#id_departments\\.0\\.teams\\.0\\.team ~ [role="form"]')
        page.click('#id_departments\\.0\\.teams\\.0\\.team ~ .remove-collection')
    page.locator('#id_company\\.name').evaluate('elem => elem.focus()')
    spy = mocker.spy(FormCollectionView, 'post')
    formset.evaluate('elem => elem.submit()')
    # since TeamCollection is fresh and empty, it should disappear before
    if viewname == 'company_1':
        expect(formset.locator('django-form-collection')).to_have_count(3)
        expect(page.locator('#id_departments\\.0\\.teams\\.0\\.team')).to_have_count(0)
    else:
        expect(formset.locator('django-form-collection')).to_have_count(4)
        expect(page.locator('#id_departments\\.0\\.teams\\.0\\.team')).to_have_count(1)
        expect(page.locator('#id_departments\\.0\\.teams\\.1\\.team')).to_have_count(0)
        expect(page.locator('#id_departments\\.1\\.department')).to_have_count(0)
    body = json.loads(spy.call_args.args[1].body)
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    expected = {
        'extra_data': {},
        'formset_data': {
            'departments': [{
                'teams': [],
                'department': {'name': 'Marketing'}
            }],
            'company': {'name': 'Pepsi'},
        },
    }
    if viewname == 'company_2':
        expected['formset_data']['departments'][0]['teams'].append(
            {'team': {'name': 'Atlanta', MARKED_FOR_REMOVAL: True}}
        )
    assert expected == body


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['company_1'])
def test_fill_collection_add_inner(page, viewname):
    formset = page.locator('django-formset')
    expect(formset.locator('django-form-collection')).to_have_count(4)
    page.fill('#id_company\\.name', "Pepsi")
    page.fill('#id_departments\\.0\\.department\\.name', "Marketing")
    page.fill('#id_departments\\.0\\.teams\\.0\\.team\\.name', "Canada")
    add_team = formset.locator('#id_departments\\.0\\.department ~ button[name="departments.0.teams.add_team"]')
    expect(add_team).to_have_text("Add Team")
    add_team.click()
    expect(formset.locator('django-form-collection')).to_have_count(5)
    page.fill('#id_departments\\.0\\.teams\\.1\\.team\\.name', "Argentina")
    page.locator('#id_company\\.name').evaluate('elem => elem.focus()')
    with page.expect_response(page.url) as response_info:
        formset.evaluate('elem => elem.submit()')
    assert response_info.value.ok is True
    expected = {
        'extra_data': {},
        'formset_data': {
            'departments': [{
                'teams': [
                    {'team': {'name': 'Canada'}},
                    {'team': {'name': 'Argentina'}}
                ],
                'department': {'name': 'Marketing'}
            }],
            'company': {'name': 'Pepsi'},
        },
    }
    assert response_info.value.request.post_data_json == expected


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['company_1', 'company_2'])
def test_fill_collection_add_outer(page, viewname):
    formset = page.locator('django-formset')
    if viewname == 'company_1':
        expect(formset.locator('django-form-collection')).to_have_count(4)
    else:
        expect(formset.locator('django-form-collection')).to_have_count(7)
    page.fill('#id_company\\.name', "Pepsi")
    page.fill('#id_departments\\.0\\.department\\.name', "Marketing")
    page.fill('#id_departments\\.0\\.teams\\.0\\.team\\.name', "Canada")
    departments_collection = formset.locator('> django-form-collection').last
    add_department = departments_collection.locator('> button[name="departments.add_department"]')
    expect(add_department).to_have_text("Add Department")
    add_department.click()
    if viewname == 'company_1':
        expect(departments_collection.locator('django-form-collection')).to_have_count(4)
    else:
        add_department.click()
        expect(departments_collection.locator('django-form-collection')).to_have_count(9)
    page.fill('#id_departments\\.1\\.department\\.name', "Finance")
    page.fill('#id_departments\\.1\\.teams\\.0\\.team\\.name', "Controlling")
    page.locator('#id_company\\.name').evaluate('elem => elem.focus()')
    with page.expect_response(page.url) as response_info:
        formset.evaluate('elem => elem.submit()')
    assert response_info.value.ok is True
    expected = {
        'extra_data': {},
        'formset_data': {
            'departments': [{
                'teams': [
                    {'team': {'name': 'Canada'}},
                ],
                'department': {'name': 'Marketing'}
            }, {
                'teams': [
                    {'team': {'name': 'Controlling'}},
                ],
                'department': {'name': 'Finance'}
            }],
            'company': {'name': 'Pepsi'},
        },
    }
    assert response_info.value.request.post_data_json == expected


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['company_3', 'company_4'])
def test_submit_half_empty_collection(page, viewname):
    formset = page.locator('django-formset')
    if viewname == 'company_3':
        expect(formset.locator('django-form-collection')).to_have_count(4)
    else:
        expect(formset.locator('django-form-collection')).to_have_count(7)
    page.fill('#id_company\\.name', "Pepsi")
    page.fill('#id_departments\\.0\\.department\\.name', "Marketing")
    page.fill('#id_departments\\.0\\.teams\\.0\\.team\\.name', "")
    page.locator('#id_company\\.name').evaluate('elem => elem.focus()')
    with page.expect_response(page.url) as response_info:
        formset.evaluate('elem => elem.submit()')
    assert response_info.value.ok is False
    expected = {
        'extra_data': {},
        'formset_data': {
            'departments': [{
                'teams': [
                    {'team': {'name': ''}},
                ],
                'department': {'name': 'Marketing'}
            }],
            'company': {'name': 'Pepsi'},
        },
    }
    assert response_info.value.request.post_data_json == expected
    assert response_info.value.json() == {
        'company': {},
        'departments': [{
            'department': {},
            'teams': [{
                'team': {'name': ['This field is required.']}
            }]
        }]
    }
