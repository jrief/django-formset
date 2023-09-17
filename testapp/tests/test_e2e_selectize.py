import pytest
import json
from time import sleep
from playwright.sync_api import expect

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
        for counter in range(1, 1000):
            label = f"Opinion {counter:04}"
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
    f'selectize{counter}': NativeFormView.as_view(
        form_class=type(f'{name}_form', (Form,), {'name': name, 'model_choice': field}),
    )
    for counter, (name, field) in enumerate(test_fields.items())
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
def test_form_validated(page, form, viewname):
    expect(page.locator('django-formset form')).to_have_count(1)
    if form.name in ['selection_required', 'static_selection', 'multi_selection']:
        expect(page.locator('django-formset form:valid')).to_have_count(0)
        expect(page.locator('django-formset form:invalid')).to_have_count(1)
    else:
        expect(page.locator('django-formset form:valid')).to_have_count(1)
        expect(page.locator('django-formset form:invalid')).to_have_count(0)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_initial_value(page, form, viewname):
    select_element = page.locator('django-formset select[is="django-selectize"]')
    expect(select_element).to_have_count(1)
    if form.name in ['selection_initialized', 'selection_required_initialized']:
        value = select_element.evaluate('elem => elem.value')
        assert value == str(get_initial_opinion().id)
    elif form.name in ['multi_selection_initialized']:
        values = select_element.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
        assert set(values) == set(str(k) for k in get_initial_opinions().values_list('id', flat=True))
    else:
        assert select_element.evaluate('elem => elem.value') == ''


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_changing_value(page, form, viewname):
    input_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    expect(input_element).to_be_visible()
    assert input_element.get_attribute('placeholder') == 'Select'
    assert input_element.evaluate('elem => elem.value') == ''
    field_group_element = page.locator('django-formset [role="group"]')
    expect(field_group_element).to_have_count(1)
    expect(field_group_element).to_have_class('dj-required dj-untouched dj-pristine')
    expect(field_group_element).not_to_have_class('dj-dirty')
    dropdown_element = page.locator('django-formset .shadow-wrapper .ts-dropdown.single')
    expect(dropdown_element).to_have_count(1)
    expect(dropdown_element).not_to_be_visible()
    input_element.click()
    expect(dropdown_element).to_be_visible()
    expect(page.locator('django-formset form:invalid')).to_have_count(1)
    pseudo_option = dropdown_element.locator('div[data-selectable]').nth(8)
    expect(pseudo_option).to_be_visible()
    initial_opinion = get_initial_opinion()
    assert pseudo_option.get_attribute('data-value') == str(initial_opinion.id)
    expect(pseudo_option).to_have_text(initial_opinion.label)
    pseudo_option.click()
    expect(field_group_element).to_have_class('dj-required dj-touched dj-dirty')
    expect(dropdown_element).to_be_hidden()
    expect(page.locator('django-formset form:valid')).to_have_count(1)
    selected_item_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control div.item')
    expect(selected_item_element).to_have_count(1)
    assert selected_item_element.get_attribute('data-value') == str(initial_opinion.id)
    expect(selected_item_element).to_have_text(initial_opinion.label)
    select_element = page.locator('django-formset select[is="django-selectize"]')
    expect(select_element).to_have_count(1)
    value = select_element.evaluate('elem => elem.value')
    assert value == str(initial_opinion.id)
    input_element.focus()
    page.keyboard.press('Backspace')
    input_element.evaluate('elem => elem.blur()')
    expect(page.locator('django-formset .shadow-wrapper .ts-input div.item')).to_have_count(0)
    expect(page.locator('django-formset form:invalid')).to_have_count(1)
    value = select_element.evaluate('elem => elem.value')
    assert value == ''


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize5'])
def test_add_multiple(page, form, viewname):
    input_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-multiple"]')
    expect(input_element).to_be_visible()
    expect(input_element).to_have_attribute('placeholder', 'Select any')
    assert input_element.evaluate('elem => elem.value') == ''
    field_group_element = page.locator('django-formset [role="group"]')
    expect(field_group_element).to_have_count(1)
    expect(field_group_element).to_have_class('dj-required dj-untouched dj-pristine')
    expect(field_group_element).not_to_have_class('dj-dirty')
    dropdown_element = page.locator('django-formset .shadow-wrapper .ts-dropdown.multi')
    expect(dropdown_element).to_have_count(1)
    expect(dropdown_element).to_be_hidden()
    input_element.click()
    expect(dropdown_element).to_be_visible()
    selected_ids = []
    pseudo_options = dropdown_element.locator('div[data-selectable]')
    for k in range(3):
        selected_ids.append(pseudo_options.nth(2).get_attribute('data-value'))
        pseudo_options.nth(2).click()
    expect(dropdown_element).to_be_visible()
    input_element.evaluate('elem => elem.blur()')
    expect(dropdown_element).to_be_hidden()
    selected_item_elements = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control div.item')
    expect(selected_item_elements).to_have_count(3)
    for k in range(3):
        expect(selected_item_elements.nth(k)).to_have_attribute('data-value', selected_ids[k])
    remove_selected_item_element = page.locator(f'django-formset .shadow-wrapper .ts-wrapper .ts-control div[data-value="{selected_ids[1]}"].item .remove')
    expect(remove_selected_item_element).to_be_visible()
    remove_selected_item_element.click()
    selected_ids.pop(1)
    selected_item_elements = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control div.item')
    expect(selected_item_elements).to_have_count(2)
    select_element = page.locator('django-formset select[is="django-selectize"]')
    expect(select_element).to_have_count(1)
    values = select_element.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
    assert set(values) == set(selected_ids)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize6'])
def test_change_multiple(page, form, viewname):
    formset_element = page.locator('django-formset')
    select_element = formset_element.locator('select[is="django-selectize"]')
    expect(select_element).to_be_visible()
    values = select_element.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
    assert len(values) == 4
    assert set(values) == set(str(i) for i in get_initial_opinions().values_list('id', flat=True))
    field_group_element = formset_element.locator('[role="group"]')
    expect(field_group_element).to_be_visible()
    expect(field_group_element).to_have_class('dj-untouched dj-pristine')
    remove_selected_item_element = formset_element.locator(f'.shadow-wrapper .ts-wrapper .ts-control div[data-value="{values[1]}"].item .remove')
    expect(remove_selected_item_element).to_be_visible()
    remove_selected_item_element.click()
    item_elements = formset_element.locator(f'.shadow-wrapper .ts-wrapper .ts-control div.item')
    expect(item_elements).to_have_count(3)
    expect(field_group_element).to_have_class('dj-untouched dj-dirty')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_lookup_value(page, mocker, form, viewname):
    input_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    expect(input_element).to_be_visible()
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
    assert content['options'][0]['label'] == "Opinion 0159"
    dropdown_element = page.locator('django-formset .shadow-wrapper .ts-dropdown.single')
    pseudo_option = dropdown_element.locator('div[data-selectable]').nth(0)
    expect(pseudo_option).to_be_visible()
    expect(pseudo_option).to_have_text("Opinion 0159")


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_missing(page, view, form, viewname):
    page.locator('django-formset').evaluate('elem => elem.submit()')
    placeholder = page.locator('[role="group"] ul.dj-errorlist > li.dj-placeholder')
    expect(placeholder).to_have_text(str(Field.default_error_messages['required']))


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_value(page, mocker, view, form, viewname):
    input_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    expect(input_element).to_be_visible()
    input_element.click()
    dropdown_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-dropdown.single')
    expect(dropdown_element).to_be_visible()
    pseudo_option = dropdown_element.locator('div[data-selectable]').nth(8)
    expect(pseudo_option).to_be_visible()
    pseudo_option.click()
    spy = mocker.spy(view.view_class, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['model_choice'] == str(get_initial_opinion().id)
    assert spy.spy_return.status_code == 200
    response = json.loads(spy.spy_return.content)
    assert response['success_url'] == view.view_class.success_url


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize1'])
def test_submit_invalid(page, mocker, view, form, viewname):
    input_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    expect(input_element).to_be_visible()
    input_element.click()
    dropdown_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-dropdown.single')
    expect(dropdown_element).to_be_visible()
    pseudo_option = dropdown_element.locator('div[data-selectable]').nth(8)
    expect(pseudo_option).to_be_visible()
    pseudo_option.click()
    initial_opinion = get_initial_opinion()
    initial_opinion.tenant = 2  # this makes the selected option invalid
    initial_opinion.save(update_fields=['tenant'])
    spy = mocker.spy(view.view_class, 'post')
    page.locator('django-formset').evaluate('elem => elem.submit()')
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['model_choice'] == str(initial_opinion.id)
    assert spy.spy_return.status_code == 422
    response = json.loads(spy.spy_return.content)
    error_message = models.ModelChoiceField.default_error_messages['invalid_choice']
    assert response == {'model_choice': [error_message]}
    placeholder = page.locator('[role="group"] ul.dj-errorlist > li.dj-placeholder')
    expect(placeholder).to_have_text(str(error_message))
    initial_opinion.tenant = 1  # reset to initial tenant
    initial_opinion.save(update_fields=['tenant'])


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize0', 'selectize2', 'selectize4'])
def test_reset_selectize(page, view, form, viewname):
    select_element = page.locator('django-formset select[is="django-selectize"]')
    expect(select_element).to_be_visible()
    initial_value = select_element.evaluate('elem => elem.value')
    input_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    expect(input_element).to_be_visible()
    if form.name in ['selection', 'static_selection']:
        input_element.click()
        dropdown_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-dropdown.single')
        expect(dropdown_element).to_be_visible()
        page.locator('div[data-selectable]').nth(6).click()
    else:
        input_element.focus()
        page.keyboard.press('Backspace')
    input_element.evaluate('elem => elem.blur()')
    value = select_element.evaluate('elem => elem.value')
    assert value != initial_value
    page.locator('django-formset').evaluate('elem => elem.reset()')
    value = select_element.evaluate('elem => elem.value')
    assert value == initial_value


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectize0'])
def test_touch_selectize(page, form, viewname):
    field_group = page.locator('django-formset [role="group"]')
    expect(field_group).to_have_class('dj-untouched dj-pristine')
    placeholder = page.locator('django-formset ul.dj-errorlist > li.dj-placeholder')
    expect(placeholder).to_have_text('')
    input_element = page.locator('django-formset .shadow-wrapper .ts-wrapper .ts-control input[type="select-one"]')
    expect(input_element).to_be_visible()
    input_element.focus()
    expect(field_group).to_have_class('dj-pristine dj-touched')
    page.locator('django-formset').evaluate('elem => elem.reset()')
    expect(field_group).to_have_class('dj-pristine dj-untouched')
