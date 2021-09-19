import pytest
import json
from time import sleep

from django.forms import Field, Form, models
from django.urls import path

from formset.views import FormView
from formset.widgets import Selectize

from testapp.models import ChoicesModel


def get_initial_option():
    return ChoicesModel.objects.filter(tenant=1)[8]


@pytest.fixture
@pytest.mark.django_db
def initial_option():
    return get_initial_option()


test_fields = dict(
    selection=models.ModelChoiceField(
        label="Choose Option",
        queryset=ChoicesModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=False,
    ),
    selection_required = models.ModelChoiceField(
        label="Choose Option",
        queryset=ChoicesModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=True,
    ),
    selection_initialized=models.ModelChoiceField(
        label="Choose Option",
        queryset=ChoicesModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=False,
        initial=get_initial_option,
    ),
    selection_required_initialized=models.ModelChoiceField(
        label="Choose Option",
        queryset=ChoicesModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=True,
        initial=get_initial_option,
    ),
)

views = {
    f'selectize{ctr}': FormView.as_view(
        template_name='tests/form_with_button.html',
        form_class=type(f'{tpl[0]}_form', (Form,), {'name': tpl[0], 'model_choice': tpl[1]}),
        success_url='/success',
    )
    for ctr, tpl in enumerate(test_fields.items())
}

urlpatterns = [path(name, view, name=name) for name, view in views.items()]


@pytest.fixture
def view(viewname):
    return views[viewname]


@pytest.fixture
def form(view):
    return view.view_initkwargs['form_class']()


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_form_validated(page, form):
    assert page.query_selector('django-formset form') is not None
    if form.name == 'selection_required':
        assert page.query_selector('django-formset form:valid') is None
        assert page.query_selector('django-formset form:invalid') is not None
    else:
        assert page.query_selector('django-formset form:valid') is not None
        assert page.query_selector('django-formset form:invalid') is None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_initial_value(page, form, initial_option):
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    value = select_element.evaluate('elem => elem.value')
    if 'initialized' in form.name:
        assert value == str(initial_option.id)
    else:
        assert value == ''


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_changing_value(page, form, initial_option):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-input input[type="select-one"]')
    assert input_element is not None
    assert input_element.is_visible()
    assert input_element.get_attribute('placeholder') == 'Select'
    assert input_element.evaluate('elem => elem.value') == ''
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.single')
    assert dropdown_element is not None
    assert dropdown_element.is_hidden()
    input_element.click()
    assert dropdown_element.is_visible()
    assert page.query_selector('django-formset form:invalid') is not None
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(9)')
    assert pseudo_option.is_visible()
    assert pseudo_option.get_attribute('data-value') == str(initial_option.id)
    assert pseudo_option.inner_text() == initial_option.label
    pseudo_option.click()
    assert dropdown_element.is_hidden()
    assert page.query_selector('django-formset form:valid') is not None
    selected_item_element = page.query_selector('django-formset .shadow-wrapper .ts-input div.item')
    assert selected_item_element is not None
    assert selected_item_element.get_attribute('data-value') == str(initial_option.id)
    assert selected_item_element.inner_text() == initial_option.label
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    value = select_element.evaluate('elem => elem.value')
    assert value == str(initial_option.id)
    input_element.focus()
    page.keyboard.press('Backspace')
    input_element.evaluate('elem => elem.blur()')
    assert page.query_selector('django-formset .shadow-wrapper .ts-input div.item') is None
    assert page.query_selector('django-formset form:invalid') is not None
    value = select_element.evaluate('elem => elem.value')
    assert value == ''


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_lookup_value(page, mocker, form):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-input input[type="select-one"]')
    assert input_element is not None
    input_element.click()
    spy = mocker.spy(FormView, 'get')
    page.keyboard.press('9')
    page.keyboard.press('9')
    page.keyboard.press('9')
    sleep(1)  # because TomSelect delays the lookup
    assert spy.spy_return.status_code == 200
    content = json.loads(spy.spy_return.content)
    assert content['count'] == 1
    assert content['items'][0]['label'] == "Option 999"
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.single')
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(1)')
    assert pseudo_option is not None
    pseudo_option.inner_text() == "Option 999"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_missing(page, view, form):
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == Field.default_error_messages['required']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_value(page, mocker, view, form, initial_option):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-input input[type="select-one"]')
    assert input_element is not None
    input_element.click()
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.single')
    assert dropdown_element is not None
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(9)')
    assert pseudo_option is not None
    pseudo_option.click()
    spy = mocker.spy(view.view_class, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request[form.name]['model_choice'] == str(initial_option.id)
    assert spy.spy_return.status_code == 200
    response = json.loads(spy.spy_return.content)
    assert response['success_url'] == view.view_initkwargs['success_url']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_invalid(page, mocker, view, form, initial_option):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-input input[type="select-one"]')
    assert input_element is not None
    input_element.click()
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.single')
    assert dropdown_element is not None
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(9)')
    assert pseudo_option is not None
    pseudo_option.click()
    initial_option.tenant = 2  # this makes the selected option invalid
    initial_option.save(update_fields=['tenant'])
    spy = mocker.spy(view.view_class, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request[form.name]['model_choice'] == str(initial_option.id)
    assert spy.spy_return.status_code == 422
    response = json.loads(spy.spy_return.content)
    error_message = models.ModelChoiceField.default_error_messages['invalid_choice']
    assert response == {'selection_required': {'model_choice': [error_message]}}
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == error_message
    initial_option.tenant = 1  # reset to initial tenant
    initial_option.save(update_fields=['tenant'])
