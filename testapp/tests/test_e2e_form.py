import pytest
from time import sleep
from playwright.sync_api import expect

from django.core.exceptions import ValidationError
from django.forms import fields, forms
from django.urls import path

from formset.views import FormView

from .utils import ContextMixin, get_javascript_catalog


class FullNameForm(forms.Form):
    full_name = fields.RegexField(
        r'\w+\s+\w+',
        label="Full name",
        min_length=2,
        max_length=100,
        help_text="Please enter at least two characters",
    )

    def clean(self):
        cleaned_data = super().clean()
        parts = cleaned_data['full_name'].split()
        if len(parts) < 2:
            raise ValidationError("A valid full name consists of at least a first- and a last name.")
        for part in parts:
            if not part[0].isupper() or not part[1:].islower():
                raise ValidationError("Names have invalid capitalization.")
        return cleaned_data


class DemoFormView(ContextMixin, FormView):
    template_name = 'testapp/native-form.html'
    form_class=FullNameForm
    success_url = '/success'
    extra_context = {'click_actions': 'submit -> proceed'}


urlpatterns = [
    path('full_name', DemoFormView.as_view(), name='full_name'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['full_name'])
def test_field_required_error(page, viewname):
    submit_button = page.locator('button[df-click]').first
    submit_button.click()
    error_placeholder = page.locator('#id_full_name + .dj-field-errors > .dj-errorlist > .dj-placeholder')
    expect(error_placeholder).to_have_text("This field is required.")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['full_name'])
def test_field_pattern_error(page, viewname):
    input_field = page.locator('#id_full_name')
    input_field.type("jane")
    submit_button = page.locator('button[df-click]').first
    submit_button.click()
    error_placeholder = page.locator('#id_full_name + .dj-field-errors > .dj-errorlist > .dj-placeholder')
    expect(error_placeholder).to_have_text("Enter a valid value.")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['full_name'])
def test_form_submission_error(page, viewname):
    input_field = page.locator('#id_full_name')
    input_field.type("jane miller")
    submit_button = page.locator('button[df-click]').first
    submit_button.click()
    sleep(0.2)
    error_placeholder = page.locator('#id_fullnameform + .dj-form .dj-form-errors > .dj-errorlist > .dj-placeholder')
    expect(error_placeholder).to_have_text("Names have invalid capitalization.")
