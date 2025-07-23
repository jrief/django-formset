import pytest
from playwright.sync_api import expect

from django.forms import fields, forms
from django.urls import path

from formset.validators import phone_number_validator
from formset.views import FormView
from formset.widgets import PhoneNumberInput

from .utils import ContextMixin, get_javascript_catalog


class PhoneForm(forms.Form):
    phone_number = fields.CharField(
        label="Phone Number",
        validators=[phone_number_validator],
        widget=PhoneNumberInput,
    )


class DemoFormView(ContextMixin, FormView):
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
def test_phone_number_valid(page, viewname):
    input_field = page.locator('django-formset input[is="django-phone-number"]')
    edit_field = input_field.locator('+ [role="textbox"] .phone-number-edit')
    edit_field.fill('+1 212 234 5678')
    edit_field.evaluate('elem => elem.blur()')
    error_list = input_field.locator('~ [role="alert"] .dj-errorlist')
    expect(error_list).to_have_count(1)
    with page.expect_response(page.url) as response_info:
        page.locator('django-formset').evaluate('elem => elem.submit()')
    assert response_info.value.ok is True
    request = response_info.value.request.post_data_json
    assert request['formset_data']['phone_number'] == "+12122345678"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['landline'])
def test_phone_number_setter(page, viewname):
    input_field = page.locator('django-formset input[is="django-phone-number"]')
    edit_field = input_field.locator('+ [role="textbox"] .phone-number-edit')
    expect(edit_field).to_have_text("")
    input_field.evaluate('elem => elem.value = "+12122345678"')
    expect(input_field).to_have_value("+12122345678")
    expect(edit_field).to_have_text("+1 212 234 5678")
    input_field.evaluate('elem => elem.value = "nonsense"')
    expect(input_field).to_have_value("nonsense")
    expect(edit_field).to_have_text("")
