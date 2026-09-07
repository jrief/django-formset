import pytest
from datetime import date
from playwright.sync_api import expect

from django.forms import fields, Form
from django.urls import reverse

from testapp.models import Company, PersonModel


class SampleForm(Form):
    enter = fields.CharField(min_length=2)


@pytest.mark.django_db
@pytest.mark.parametrize('viewname', ['admin:testapp_personmodel_add'])
@pytest.mark.parametrize('nth_save', range(3))
def test_admin_edit_person(live_server, page, viewname, nth_save, subtests):
    page.locator('#id_full_name').fill("John Doe")
    page.locator('#id_activity_days').fill("123")
    page.locator('#id_gender_1').check()
    page.locator('#id_birth_date + [role="textbox"] [aria-placeholder="yyyy"]').fill("1975")
    page.locator('#id_birth_date + [role="textbox"] [aria-placeholder="mm"]').fill("05")
    page.locator('#id_birth_date + [role="textbox"] [aria-placeholder="dd"]').fill("25")
    page.locator('#id_continent').select_option('2')
    page.locator('#id_annotation').focus()
    expect(page.locator('#id_annotation')).to_be_focused()
    with page.expect_response(page.url) as response_info:
        page.locator('.submit-row > button[type="button"]').nth(nth_save).click()
    assert response_info.value.ok is True
    person = PersonModel.objects.order_by('id').last()
    assert person.full_name == "John Doe"
    assert person.gender == 'male'
    assert person.extra_data.get('activity_days') == 123
    assert person.birth_date == date(year=1975, month=5, day=25)
    assert person.get_continent_display() == "Europe"
    if nth_save == 0:
        next_view_url = reverse('admin:testapp_personmodel_changelist')
    elif nth_save == 1:
        next_view_url = reverse('admin:testapp_personmodel_add')
    elif nth_save == 2:
        next_view_url = reverse('admin:testapp_personmodel_change', kwargs={'object_id': person.id})
    else:
        raise ValueError(f"Invalid nth_save value: {nth_save}")
    expect(page).to_have_url(f'{live_server.url}{next_view_url}')
    if nth_save != 2:
        return

    with subtests.test("edit the person again"):
        page.wait_for_load_state('domcontentloaded')
        page.locator('#id_full_name').fill("Jane Doe")
        page.locator('#id_activity_days').fill("321")
        page.locator('#id_gender_0').check()
        with page.expect_response(f'{live_server.url}{next_view_url}') as response_info:
            page.locator('.submit-row > button[type="button"]').nth(nth_save).click()
        assert response_info.value.ok is True
        person.refresh_from_db()
        assert person.full_name == "Jane Doe"
        assert person.gender == 'female'
        assert person.extra_data.get('activity_days') == 321


@pytest.mark.django_db
@pytest.mark.parametrize('viewname', ['admin:testapp_company_add'])
@pytest.mark.parametrize('nth_save', range(3))
def test_admin_edit_company(live_server, page, viewname, nth_save, subtests):
    page.locator('#id_company\\.name').fill("Red Bull")
    page.locator('#id_departments\\.0\\.department\\.name').fill("Marketing")
    page.locator('#id_departments\\.0\\.teams\\.0\\.team\\.name').fill("Action Sports")
    page.locator('#id_departments\\.0\\.teams\\.0\\.team\\.name').blur()
    with page.expect_response(page.url) as response_info:
        page.locator('.submit-row > button[type="button"]').nth(nth_save).click()
    assert response_info.value.ok is True
    company = Company.objects.order_by('id').last()
    assert company.name == "Red Bull"
    assert company.departments.count() == 1
    assert company.departments.first().name == "Marketing"
    assert company.departments.first().teams.count() == 1
    assert company.departments.first().teams.first().name == "Action Sports"
    if nth_save == 0:
        next_view_url = reverse('admin:testapp_company_changelist')
    elif nth_save == 1:
        next_view_url = reverse('admin:testapp_company_add')
    elif nth_save == 2:
        next_view_url = reverse('admin:testapp_company_change', kwargs={'object_id': company.id})
    else:
        raise ValueError(f"Invalid nth_save value: {nth_save}")
    expect(page).to_have_url(f'{live_server.url}{next_view_url}')
    if nth_save != 2:
        return

    with subtests.test("edit the company again"):
        page.wait_for_load_state('domcontentloaded')
        page.locator('#id_departments\\.0\\.teams\\.1\\.team\\.name').fill("Web Services")
        page.locator('#id_departments\\.1\\.department\\.name').fill("Finance")
        page.locator('#id_departments\\.1\\.teams\\.0\\.team\\.name').fill("Controlling")
        with page.expect_response(f'{live_server.url}{next_view_url}') as response_info:
            page.locator('.submit-row > button[type="button"]').nth(nth_save).click()
        assert response_info.value.ok is True
        company.refresh_from_db()
        assert company.departments.order_by('id').first().teams.order_by('id').last().name == "Web Services"
        assert company.departments.order_by('id').last().name == "Finance"
        assert company.departments.order_by('id').last().teams.first().name == "Controlling"
