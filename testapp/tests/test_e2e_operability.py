import pytest
from playwright.sync_api import expect

from django.forms.forms import Form
from django.forms.fields import BooleanField, CharField, ChoiceField
from django.forms.widgets import CheckboxInput, TextInput, RadioSelect
from django.urls import path

from formset.views import FormView

from .utils import get_javascript_catalog


class QuestionnaireForm(Form):
    full_name = CharField(
        widget=TextInput(attrs={'df-disable': ".gender=='x'"}),
    )
    gender = ChoiceField(
        choices=[('m', "Male"), ('f', "Female"), ('x', "Inapplicable")],
        widget=RadioSelect,
    )
    pregnant = BooleanField(
        required=False,
        widget=CheckboxInput(attrs={'df-show': ".gender=='f'"})
    )


urlpatterns = [
    path('questionnaire', FormView.as_view(
        form_class=QuestionnaireForm,
        template_name='testapp/native-form.html',
        success_url='/success',
    ), name='questionnaire'),
    path('questionnaire_initial_male', FormView.as_view(
        form_class=QuestionnaireForm,
        template_name='testapp/native-form.html',
        initial={'full_name': "John Doe", 'gender': 'm'},
    ), name='questionnaire_initial_male'),
    path('questionnaire_initial_female', FormView.as_view(
        form_class=QuestionnaireForm,
        template_name='testapp/native-form.html',
        initial={'full_name': "Johanna Doe", 'gender': 'f'},
    ), name='questionnaire_initial_female'),
    path('questionnaire_initial_inapplicable', FormView.as_view(
        form_class=QuestionnaireForm,
        template_name='testapp/native-form.html',
        initial={'full_name': "Company Ltd.", 'gender': 'x'},
    ), name='questionnaire_initial_inapplicable'),
    get_javascript_catalog(),
]


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['questionnaire'])
def test_show_checkbox(page, viewname):
    input_full_name = page.locator('#id_full_name')
    radio_male = page.locator('#id_gender_0')
    radio_female = page.locator('#id_gender_1')
    radio_inapplicable = page.locator('#id_gender_2')
    checkbox_pregnant = page.locator('#id_pregnant')
    expect(input_full_name).to_be_visible()
    expect(input_full_name).not_to_be_disabled()
    expect(radio_male).to_be_visible()
    expect(radio_female).to_be_visible()
    expect(radio_inapplicable).to_be_visible()
    expect(checkbox_pregnant).not_to_be_visible()
    radio_female.click()
    expect(checkbox_pregnant).to_be_visible()
    radio_male.click()
    expect(checkbox_pregnant).not_to_be_visible()
    radio_inapplicable.click()
    expect(input_full_name).to_be_disabled()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['questionnaire_initial_male'])
def test_show_checkbox_male(page, viewname):
    radio_female = page.locator('#id_gender_1')
    checkbox_pregnant = page.locator('#id_pregnant')
    expect(checkbox_pregnant).not_to_be_visible()
    radio_female.click()
    expect(checkbox_pregnant).to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['questionnaire_initial_female'])
def test_show_checkbox_female(page, viewname):
    radio_male = page.locator('#id_gender_0')
    checkbox_pregnant = page.locator('#id_pregnant')
    expect(checkbox_pregnant).to_be_visible()
    radio_male.click()
    expect(checkbox_pregnant).not_to_be_visible()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['questionnaire_initial_inapplicable'])
def test_show_checkbox_inapplicable(page, viewname):
    input_full_name = page.locator('#id_full_name')
    radio_male = page.locator('#id_gender_0')
    expect(input_full_name).to_be_disabled()
    radio_male.click()
    expect(input_full_name).not_to_be_disabled()
