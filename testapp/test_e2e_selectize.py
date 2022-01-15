import pytest
import json
from time import sleep

from django.forms import Field, Form, fields, models
from django.urls import path

from formset.views import FormView
from formset.widgets import Selectize, SelectizeMultiple

from testapp.models import OpinionModel


class NativeFormView(FormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


@pytest.fixture(scope='function')
def django_db_setup(django_db_blocker):
    with django_db_blocker.unblock():
        for counter in range(1, 200):
            label = f"Opinion {counter}"
            OpinionModel.objects.update_or_create(tenant=1, label=label)


def get_initial_opinion():
    return OpinionModel.objects.filter(tenant=1)[8]


def get_initial_opinions():
    return OpinionModel.objects.filter(tenant=1)[48:52]


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
    static_selection=fields.ChoiceField(
        choices=lambda: OpinionModel.objects.filter(tenant=1).values_list('id', 'label')[:100],
        widget=Selectize,
        required=True,
    ),
    multi_selection=models.ModelMultipleChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=SelectizeMultiple(search_lookup='label__icontains', placeholder="Select any"),
        required=True,
    ),
    multi_selection_initialized=models.ModelMultipleChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=SelectizeMultiple(search_lookup='label__icontains', placeholder="Select any"),
        required=False,
        initial=get_initial_opinions,
    ),
)

views = {
    f'selectize{ctr}': NativeFormView.as_view(
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
    if form.name in ['selection_required', 'static_selection', 'multi_selection']:
        assert page.query_selector('django-formset form:valid') is None
        assert page.query_selector('django-formset form:invalid') is not None
    else:
        assert page.query_selector('django-formset form:valid') is not None
        assert page.query_selector('django-formset form:invalid') is None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_initial_value(page, form):
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    value = select_element.evaluate('elem => elem.getValue()')
    if form.name in ['selection_initialized', 'selection_required_initialized']:
        assert value == str(get_initial_opinion().id)
    elif form.name in ['multi_selection_initialized']:
        assert set(value) == set(str(k) for k in get_initial_opinions().values_list('id', flat=True))
    else:
        assert not value


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_changing_value(page, form):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
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
    initial_opinion = get_initial_opinion()
    assert pseudo_option.get_attribute('data-value') == str(initial_opinion.id)
    assert pseudo_option.inner_text() == initial_opinion.label
    pseudo_option.click()
    assert 'dj-pristine' not in field_group_element.get_attribute('class')
    assert 'dj-dirty' in field_group_element.get_attribute('class')
    assert dropdown_element.is_hidden()
    assert page.query_selector('django-formset form:valid') is not None
    selected_item_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-control div.item')
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
@pytest.mark.parametrize('viewname', ['selectize5'])
def test_add_multiple(page, form):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-multiple"]')
    assert input_element is not None
    assert input_element.is_visible()
    assert input_element.get_attribute('placeholder') == 'Select any'
    assert input_element.evaluate('elem => elem.value') == ''
    field_group_element = page.query_selector('django-formset django-field-group')
    assert field_group_element is not None
    assert 'dj-pristine' in field_group_element.get_attribute('class')
    assert 'dj-untouched' in field_group_element.get_attribute('class')
    assert 'dj-dirty' not in field_group_element.get_attribute('class')
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-dropdown.multi')
    assert dropdown_element is not None
    assert dropdown_element.is_hidden()
    input_element.click()
    assert dropdown_element.is_visible()
    selected_ids = []
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(3)')
    selected_ids.append(pseudo_option.get_attribute('data-value'))
    pseudo_option.click()
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(3)')
    pseudo_option.click()
    selected_ids.append(pseudo_option.get_attribute('data-value'))
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(3)')
    pseudo_option.click()
    selected_ids.append(pseudo_option.get_attribute('data-value'))
    assert dropdown_element.is_visible()
    input_element.evaluate('elem => elem.blur()')
    assert dropdown_element.is_hidden()
    selected_item_elements = page.query_selector_all('django-formset .shadow-wrapper .ts-wrapper .ts-control div.item')
    assert len(selected_item_elements) == 3
    assert selected_item_elements[1].get_attribute('data-value') == selected_ids[1]
    remove_selected_item_element = page.query_selector(f'django-formset .shadow-wrapper .ts-wrapper .ts-control div[data-value="{selected_ids[1]}"].item .remove')
    assert remove_selected_item_element is not None
    remove_selected_item_element.click()
    selected_ids.pop(1)
    selected_item_elements = page.query_selector_all('django-formset .shadow-wrapper .ts-wrapper .ts-control div.item')
    assert len(selected_item_elements) == 2
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    value = select_element.evaluate('elem => elem.getValue()')
    assert value == selected_ids


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize6'])
def test_change_multiple(page, form):
    formset_element = page.query_selector('django-formset')
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    value = select_element.evaluate('elem => elem.getValue()')
    assert len(value) == 4
    assert set(value) == set(str(i) for i in get_initial_opinions().values_list('id', flat=True))
    field_group_element = page.query_selector('django-formset django-field-group')
    assert field_group_element is not None
    assert 'dj-pristine' in field_group_element.get_attribute('class')
    assert 'dj-untouched' in field_group_element.get_attribute('class')
    assert 'dj-dirty' not in field_group_element.get_attribute('class')
    remove_selected_item_element = formset_element.query_selector(f'.shadow-wrapper .ts-wrapper .ts-control div[data-value="{value[1]}"].item .remove')
    assert remove_selected_item_element is not None
    remove_selected_item_element.click()
    item_elements = formset_element.query_selector_all(f'.shadow-wrapper .ts-wrapper .ts-control div.item')
    assert len(item_elements) == 3
    assert 'dj-dirty' in field_group_element.get_attribute('class')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_lookup_value(page, mocker, form):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    assert input_element is not None
    input_element.click()
    spy = mocker.spy(FormView, 'get')
    page.keyboard.press('1')
    page.keyboard.press('5')
    page.keyboard.press('9')
    sleep(1)  # because TomSelect delays the lookup
    assert spy.called is True
    assert spy.spy_return.status_code == 200
    content = json.loads(spy.spy_return.content)
    assert content['count'] == 1
    assert content['items'][0]['label'] == "Opinion 159"
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
def test_submit_value(page, mocker, view, form):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    assert input_element is not None
    input_element.click()
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-dropdown.single')
    assert dropdown_element is not None
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(9)')
    assert pseudo_option is not None
    pseudo_option.click()
    spy = mocker.spy(view.view_class, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['model_choice'] == str(get_initial_opinion().id)
    assert spy.spy_return.status_code == 200
    response = json.loads(spy.spy_return.content)
    assert response['success_url'] == view.view_class.success_url


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_invalid(page, mocker, view, form):
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    assert input_element is not None
    input_element.click()
    dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper  .ts-dropdown.single')
    assert dropdown_element is not None
    pseudo_option = dropdown_element.query_selector('div[data-selectable]:nth-child(9)')
    assert pseudo_option is not None
    pseudo_option.click()
    initial_opinion = get_initial_opinion()
    initial_opinion.tenant = 2  # this makes the selected option invalid
    initial_opinion.save(update_fields=['tenant'])
    spy = mocker.spy(view.view_class, 'post')
    page.wait_for_selector('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['model_choice'] == str(initial_opinion.id)
    assert spy.spy_return.status_code == 422
    response = json.loads(spy.spy_return.content)
    error_message = models.ModelChoiceField.default_error_messages['invalid_choice']
    assert response == {'model_choice': [error_message]}
    placeholder_text = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder').inner_text()
    assert placeholder_text == error_message
    initial_opinion.tenant = 1  # reset to initial tenant
    initial_opinion.save(update_fields=['tenant'])


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize0', 'selectize2', 'selectize4'])
def test_reset_formset(page, view, form):
    select_element = page.query_selector('django-formset select[is="django-selectize"]')
    assert select_element is not None
    initial_value = select_element.evaluate('elem => elem.getValue()')
    input_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    assert input_element.is_visible()
    if form.name in ['selection', 'static_selection']:
        input_element.click()
        dropdown_element = page.query_selector('django-formset .shadow-wrapper .ts-wrapper .ts-dropdown.single')
        assert dropdown_element.is_visible()
        page.wait_for_selector('div[data-selectable]:nth-child(7)').click()
    else:
        input_element.focus()
        page.keyboard.press('Backspace')
    input_element.evaluate('elem => elem.blur()')
    value = select_element.evaluate('elem => elem.getValue()')
    assert value != initial_value
    page.wait_for_selector('django-formset').evaluate('elem => elem.reset()')
    value = select_element.evaluate('elem => elem.getValue()')
    assert value == initial_value
