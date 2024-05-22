from time import sleep
import json
import pytest
from playwright.sync_api import expect

from django.forms import fields, forms
from django.urls import path

from formset.validators import phone_number_validator
from formset.views import FormView
from formset.widgets import PhoneNumberInput

from .utils import get_javascript_catalog


class PhoneForm(forms.Form):
    phone_number = fields.CharField(
        label="Phone Number",
        validators=[phone_number_validator],
        widget=PhoneNumberInput,
    )


class DemoFormView(FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


urlpatterns = [
    path('landline', DemoFormView.as_view(form_class=PhoneForm), name='landline'),
    path('national', DemoFormView.as_view(form_class=PhoneForm), name='national'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['landline'])
def test_phone_number_required(page, viewname):
    input_field = page.locator('django-formset input[is="django-phone-number"]')
    edit_field = input_field.locator('+ [role="textbox"] .phone-number-edit')
    expect(input_field).not_to_be_visible()
    expect(edit_field).to_be_visible()
    edit_field.focus()
    edit_field.evaluate('elem => elem.blur()')
    error_list = input_field.locator('~ [role="alert"] .dj-errorlist')
    expect(error_list).to_have_text("This field is required.")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['landline'])
def test_phone_number_invalid(page, viewname):
    input_field = page.locator('django-formset input[is="django-phone-number"]')
    edit_field = input_field.locator('+ [role="textbox"] .phone-number-edit')
    edit_field.fill('+123456789')
    edit_field.evaluate('elem => elem.blur()')
    error_list = input_field.locator('~ [role="alert"] .dj-errorlist')
    expect(error_list).to_have_text("Please enter a valid phone number.")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['landline'])
def test_phone_number_valid(page, mocker, viewname):
    input_field = page.locator('django-formset input[is="django-phone-number"]')
    edit_field = input_field.locator('+ [role="textbox"] .phone-number-edit')
    edit_field.fill('+1 212 234 5678')
    edit_field.evaluate('elem => elem.blur()')
    error_list = input_field.locator('~ [role="alert"] .dj-errorlist')
    expect(error_list).to_have_count(1)
    spy = mocker.spy(DemoFormView, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    sleep(0.2)
    spy.assert_called()
    assert spy.spy_return.status_code == 200
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['phone_number'] == "+12122345678"
