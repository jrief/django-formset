import json
import pytest
import re
from playwright.sync_api import expect
from time import sleep
from timeit import default_timer as timer


from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import fields, Form
from django.http.response import HttpResponseForbidden

from formset.admin import ModelAdmin

from testapp.forms.person import ModelPersonForm
from testapp.models import PersonModel
from .utils import ContextMixin, get_javascript_catalog


class SampleForm(Form):
    enter = fields.CharField(min_length=2)


# @admin.register(PersonModel)
# class PersonAdmin(ModelAdmin):
#     form = ModelPersonForm


# urlpatterns = [
#     path('person_admin', FormCollectionView.as_view(
#         collection_class=CompanyCollection0,
#         template_name='testapp/form-collection.html',
#         extra_context={'click_actions': 'submit -> proceed', 'force_submission': True},
#     ), name='company_1'),


@pytest.mark.django_db
@pytest.mark.parametrize('viewname', ['admin:testapp_personmodel_add'])
@pytest.mark.parametrize('nth_save', [0])
def test_person_admin(page, viewname, nth_save):
    page.locator('#id_full_name').fill("John Doe")
    page.locator('#id_activity_days').fill("123")
    page.locator('#id_gender_1').check()
    page.locator('#id_birth_date + [role="textbox"] [aria-placeholder="yyyy"]').fill("1975")
    page.locator('#id_birth_date + [role="textbox"] [aria-placeholder="mm"]').fill("05")
    page.locator('#id_birth_date + [role="textbox"] [aria-placeholder="dd"]').fill("25")
    page.locator('#id_continent').select_option('2')
    page.locator('#id_annotation').focus()
    page.screenshot(path='personadmin.png')
    with page.expect_response(page.url) as response_info:
        page.locator('.submit-row > button[type="button"]').nth(nth_save).click()
    assert response_info.value.ok is True
    assert response_info.value.json() == {'success_url': '/success'}

    sleep(100)
