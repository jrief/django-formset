import pytest
import json
from time import sleep

from django.forms import Field, Form, models
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from formset.views import FormView
from formset.widgets import Selectize

from testapp.models import OpinionModel


@method_decorator(csrf_exempt, name='dispatch')
class SampleFormView(FormView):
    template_name = 'testapp/form-groups.html'
    success_url = '/success'


@pytest.fixture(scope='function')
def django_db_setup(django_db_blocker):
    with django_db_blocker.unblock():
        for counter in range(1, 100):
            label = f"Opinion {counter}"
            OpinionModel.objects.update_or_create(tenant=1, label=label)


def get_initial_opinion():
    return OpinionModel.objects.filter(tenant=1)[8]


@pytest.fixture
@pytest.mark.django_db
def initial_opinion():
    yield get_initial_opinion()


test_fields = dict(
    selection=models.ModelChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=False,
    ),
    selection_required = models.ModelChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=True,
    ),
    selection_initialized=models.ModelChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=False,
        initial=get_initial_opinion,
    ),
    selection_required_initialized=models.ModelChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=Selectize(search_lookup='label__icontains'),
        required=True,
        initial=get_initial_opinion,
    ),
)

views = {
    f'selectize{ctr}': SampleFormView.as_view(
        form_class=type(f'{tpl[0]}_form', (Form,), {'name': tpl[0], 'model_choice': tpl[1]}),
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
def test_initial_value(page, form, initial_opinion):
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    value = select_element.evaluate('elem => elem.value')
    if 'initialized' in form.name:
        assert value == str(initial_opinion.id)
    else:
        assert value == ''


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_changing_value(page, form, initial_opinion):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-input input[type="select-one"]')
    assert input_element is not None
    assert input_element.is_visible()
    assert input_element.get_attribute('placeholder') == 'Select'
    assert input_element.evaluate('elem => elem.value') == ''
    field_group_element = page.query_selector('django-formset django-field-group')
    assert field_group_element is not None
    assert 'dj-pristine' in field_group_element.get_attribute('class')
    assert 'dj-dirty' not in field_group_element.get_attribute('class')
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.single')
    assert dropdown_element is not None
    assert dropdown_element.is_hidden()
    input_element.click()
    assert dropdown_element.is_visible()
    assert page.query_selector('django-formset form:invalid') is not None
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(9)')
    assert pseudo_option.is_visible()
    assert pseudo_option.get_attribute('data-value') == str(initial_opinion.id)
    assert pseudo_option.inner_text() == initial_opinion.label
    pseudo_option.click()
    assert 'dj-pristine' not in field_group_element.get_attribute('class')
    assert 'dj-dirty' in field_group_element.get_attribute('class')
    assert dropdown_element.is_hidden()
    assert page.query_selector('django-formset form:valid') is not None
    selected_item_element = page.query_selector('django-formset .shadow-wrapper .ts-input div.item')
    assert selected_item_element is not None
    assert selected_item_element.get_attribute('data-value') == str(initial_opinion.id)
    assert selected_item_element.inner_text() == initial_opinion.label
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    value = select_element.evaluate('elem => elem.value')
    assert value == str(initial_opinion.id)
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
    sleep(1)  # because TomSelect delays the lookup
    assert spy.spy_return.status_code == 200
    content = json.loads(spy.spy_return.content)
    assert content['count'] == 1
    assert content['items'][0]['label'] == "Opinion 99"
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.single')
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(1)')
    assert pseudo_option is not None
    pseudo_option.inner_text() == "Opinion 99"


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_missing(page, view, form):
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == Field.default_error_messages['required']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_value(page, mocker, view, form, initial_opinion):
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
    assert request[form.name]['model_choice'] == str(initial_opinion.id)
    assert spy.spy_return.status_code == 200
    response = json.loads(spy.spy_return.content)
    assert response['success_url'] == view.view_class.success_url


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_invalid(page, mocker, view, form, initial_opinion):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-input input[type="select-one"]')
    assert input_element is not None
    input_element.click()
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.single')
    assert dropdown_element is not None
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(9)')
    assert pseudo_option is not None
    pseudo_option.click()
    initial_opinion.tenant = 2  # this makes the selected option invalid
    initial_opinion.save(update_fields=['tenant'])
    spy = mocker.spy(view.view_class, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request[form.name]['model_choice'] == str(initial_opinion.id)
    assert spy.spy_return.status_code == 422
    response = json.loads(spy.spy_return.content)
    error_message = models.ModelChoiceField.default_error_messages['invalid_choice']
    assert response == {'selection_required': {'model_choice': [error_message]}}
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == error_message
    initial_opinion.tenant = 1  # reset to initial tenant
    initial_opinion.save(update_fields=['tenant'])


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize0', 'selectize2'])
def test_reset_formset(page, view, form):
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    initial_value = select_element.evaluate('elem => elem.value')
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-input input[type="select-one"]')
    assert input_element.is_visible()
    if form.name == 'selection':
        input_element.click()
        dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.single')
        assert dropdown_element.is_visible()
        page.wait_for_selector('div[data-selectable]:nth-child(7)').click()
    else:
        input_element.focus()
        page.keyboard.press('Backspace')
    input_element.evaluate('elem => elem.blur()')
    value = select_element.evaluate('elem => elem.value')
    assert value != initial_value
    page.wait_for_selector('django-formset').evaluate('elem => elem.reset()')
    value = select_element.evaluate('elem => elem.value')
    assert value == initial_value
