import pytest
import json
from time import sleep

from django.forms import Form, models
from django.urls import path
from django.views.generic import UpdateView, FormView as GenericFormView

from formset.views import IncompleteSelectResponseMixin, FormViewMixin
from formset.widgets import DualSelector

from testapp.forms.poll import ModelPollForm
from testapp.models import OpinionModel, PollModel


class NativeFormView(IncompleteSelectResponseMixin, FormViewMixin, GenericFormView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'


class ModelFormView(IncompleteSelectResponseMixin, FormViewMixin, UpdateView):
    template_name = 'testapp/native-form.html'
    success_url = '/success'
    form_class = ModelPollForm
    model = PollModel

    def get_object(self, queryset=None):
        obj, _ = self.model.objects.get_or_create(created_by='testapp')
        return obj


@pytest.fixture(scope='function')
def django_db_setup(django_db_blocker):
    with django_db_blocker.unblock():
        for counter in range(1, 1000):
            label = f"Opinion {counter:04}"
            OpinionModel.objects.update_or_create(tenant=1, label=label)


def get_initial_opinion():
    return OpinionModel.objects.filter(tenant=1)[8]


def get_initial_opinions():
    return list(OpinionModel.objects.filter(tenant=1).values_list('id', flat=True)[41:55])


test_fields = dict(
    selector=models.ModelMultipleChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=DualSelector(search_lookup='label__icontains'),
        required=False,
    ),
    selector_complete=models.ModelMultipleChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1)[:100],
        widget=DualSelector(search_lookup='label__icontains'),
    ),
    selector_required=models.ModelMultipleChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=DualSelector(search_lookup='label__icontains'),
    ),
    selector_initialized=models.ModelMultipleChoiceField(
        queryset=OpinionModel.objects.filter(tenant=1),
        widget=DualSelector(search_lookup='label__icontains'),
        initial=get_initial_opinions,
    ),
)

views = {
    f'selector{counter}': NativeFormView.as_view(
        form_class=type(f'{name}_form', (Form,), {'name': name, 'model_choice': field}),
    )
    for counter, (name, field) in enumerate(test_fields.items())
}
views['selectorF'] = NativeFormView.as_view(
    form_class=type('force_submission_form', (Form,), {'name': 'force_submission_form', 'model_choice': test_fields['selector_required']}),
    extra_context={'force_submission': True},
)
views['selectorP'] = ModelFormView.as_view(
    form_class=type('model_poll_form', (ModelPollForm,), {'name': 'selector_required'}),
    extra_context={'force_submission': True},
)

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
    assert page.query_selector('django-formset form') is not None
    if form.name in ['selector', 'selector_initialized']:
        assert page.query_selector('django-formset form:valid') is not None
        assert page.query_selector('django-formset form:invalid') is None
    else:
        assert page.query_selector('django-formset form:valid') is None
        assert page.query_selector('django-formset form:invalid') is not None


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_initial_value(page, form, viewname):
    sleep(0.25)
    selector_element = page.query_selector('django-formset select[is="django-dual-selector"]')
    assert selector_element is not None
    value = selector_element.evaluate('elem => elem.value')
    if form.name == 'selector_initialized':
        assert set(value) == set(str(k) for k in get_initial_opinions())
    else:
        assert value == []


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_move_all_right(page, mocker, view, form, viewname):
    selector_element = page.query_selector('django-formset select[is="django-dual-selector"]')
    assert selector_element is not None
    incomplete = selector_element.get_attribute('incomplete') is not None
    selector_options = selector_element.query_selector_all('option')
    if form.name == 'selector_complete':
        assert incomplete is False
        assert len(selector_options) == 100
    else:
        assert incomplete is True
        assert len(selector_options) == DualSelector.max_prefetch_choices
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-all-right')
    assert button is not None
    if viewname == 'selectorP':
        select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column django-sortable-select')
    else:
        select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    assert len(select_left_element.query_selector_all('option')) + len(select_right_element.query_selector_all('option')) == len(selector_options)
    if form.name == 'selector_initialized':
        assert len(select_right_element.query_selector_all('option')) == len(get_initial_opinions())
    else:
        assert len(select_right_element.query_selector_all('option')) == 0
    spy = mocker.spy(view.view_class, 'get')
    right_option_values = set(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
    while incomplete:
        left_option_values = set(o.get_attribute('value') for o in select_left_element.query_selector_all('option'))
        button.click()  # this triggers loading of more options
        right_option_values = right_option_values.union(left_option_values)
        assert right_option_values == set(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
        assert spy.called is True
        assert spy.spy_return.status_code == 200
        content = json.loads(spy.spy_return.content)
        spy.reset_mock()
        assert len(select_left_element.query_selector_all('option')) == content['count']
        incomplete = content['incomplete']
        assert content['total_count'] == OpinionModel.objects.filter(tenant=1).count()
        if incomplete:
            assert len(selector_element.query_selector_all('option')) < content['total_count']
        else:
            assert len(selector_element.query_selector_all('option')) == content['total_count']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0', 'selector3'])
def test_move_selected_right(page, mocker, view, form, viewname):
    sleep(0.25)
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    left_option_values = set()
    for option in select_left_element.query_selector_all('option')[30:39]:
        left_option_values.add(option.get_attribute('value'))
        option.click(modifiers=['Shift'])
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    if form.name == 'selector_initialized':
        assert len(select_right_element.query_selector_all('option')) == len(get_initial_opinions())
        left_option_values.update(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
    else:
        assert len(select_right_element.query_selector_all('option')) == 0
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-selected-right')
    assert button is not None
    button.click()
    right_option_values = set(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
    assert left_option_values == right_option_values
    option = select_right_element.query_selector_all('option')[5]
    option.click()
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-selected-left')
    assert button is not None
    button.click()
    left_option_values = set(o.get_attribute('value') for o in select_left_element.query_selector_all('option'))
    right_option_values = set(o.get_attribute('value') for o in select_right_element.query_selector_all('option'))
    assert option.get_attribute('value') in left_option_values
    assert option.get_attribute('value') not in right_option_values
    spy = mocker.spy(view.view_class, 'post')
    page.wait_for_selector('django-formset > p button').click()
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    assert set(request['formset_data']['model_choice']) == right_option_values


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_infinite_scroll(page, mocker, view, form, viewname):
    selector_element = page.query_selector('django-formset select[is="django-dual-selector"]')
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option')]
    assert len(left_option_values) == DualSelector.max_prefetch_choices
    select_left_element.focus()
    spy = mocker.spy(view.view_class, 'get')
    select_left_element.select_option(left_option_values[-2])
    assert spy.called is False
    assert len(select_left_element.query_selector_all('option')) == DualSelector.max_prefetch_choices
    page.keyboard.press('ArrowDown')
    sleep(0.1)
    assert spy.called is True
    field_name = selector_element.get_attribute('name')
    params = spy.call_args.args[1].GET
    assert params['field'] == f'__default__.{field_name}'
    assert int(params['offset']) == DualSelector.max_prefetch_choices
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option')]
    assert len(left_option_values) == 2 * DualSelector.max_prefetch_choices
    response = json.loads(spy.spy_return.content)
    assert response['count'] == DualSelector.max_prefetch_choices
    assert response['incomplete'] is True
    assert isinstance(response['items'], list)
    assert len(response['items']) == response['count']
    spy.reset_mock()
    select_left_element.query_selector('option[value="{}"]'.format(left_option_values[-1])).click()
    page.keyboard.press('ArrowDown')
    sleep(0.1)
    assert spy.called is True
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option')]
    assert len(left_option_values) == 3 * DualSelector.max_prefetch_choices
    spy.reset_mock()
    select_left_element.query_selector('option[value="{}"]'.format(left_option_values[-1])).click()
    page.keyboard.press('ArrowDown')
    sleep(0.1)
    assert spy.called is True
    response = json.loads(spy.spy_return.content)
    assert response['incomplete'] is False


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_submit_valid_form(page, mocker, view, form, viewname):
    sleep(0.25)
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option')]
    select_left_element.focus()
    select_left_element.select_option(left_option_values[48:63])
    move_button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-selected-right')
    assert move_button is not None
    move_button.click()
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    assert len(select_right_element.query_selector_all('option')) == 15
    select_right_element.query_selector('option[value="{}"]'.format(left_option_values[50])).dblclick()
    assert len(select_right_element.query_selector_all('option')) == 14
    spy = mocker.spy(view.view_class, 'post')
    submit_button = page.query_selector('django-formset button[click]')
    submit_button.click()
    sleep(0.1)
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    choices = set(left_option_values[48:63])
    choices.remove(left_option_values[50])
    assert set(request['formset_data']['model_choice']) == choices
    response = json.loads(spy.spy_return.content)
    assert response['success_url'] == '/success'


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector1'])
def test_submit_invalid_form(page, mocker, view, form, viewname):
    spy = mocker.spy(view.view_class, 'post')
    submit_button = page.query_selector('django-formset button[click]')
    submit_button.click()
    assert spy.called is False
    error_ph = page.query_selector('django-formset django-field-group ul.dj-errorlist > li.dj-placeholder')
    assert error_ph is not None
    assert error_ph.text_content() == form.fields['model_choice'].error_messages['required']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectorF'])
def test_force_submit_invalid_form(page, mocker, view, form, viewname):
    spy = mocker.spy(view.view_class, 'post')
    submit_button = page.query_selector('django-formset button[click]')
    submit_button.click()
    sleep(0.1)
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['model_choice'] == []
    response = json.loads(spy.spy_return.content)
    assert response['model_choice'] == [form.fields['model_choice'].error_messages['required']]
    error_ph = page.query_selector('django-formset django-field-group ul.dj-errorlist > li.dj-placeholder')
    assert error_ph is not None
    assert error_ph.text_content() == form.fields['model_choice'].error_messages['required']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0', 'selector3'])
def test_reset_selector(page, view, form, viewname):
    selector_element = page.query_selector('django-formset select[is="django-dual-selector"]')
    assert selector_element is not None
    initial_values = selector_element.evaluate('elem => elem.value')
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option')]
    select_left_element.query_selector('option[value="{}"]'.format(left_option_values[50])).dblclick()
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    right_option_values = [o.get_attribute('value') for o in select_right_element.query_selector_all('option')]
    assert set(initial_values).union([left_option_values[50]]) == set(right_option_values)
    values = selector_element.evaluate('elem => elem.value')
    assert values != initial_values
    page.wait_for_selector('django-formset').evaluate('elem => elem.reset()')
    values = selector_element.evaluate('elem => elem.value')
    assert values == initial_values


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_touch_selector(page, form, viewname):
    field_group = page.query_selector('django-formset django-field-group')
    assert 'dj-untouched' in field_group.get_attribute('class')
    assert 'dj-pristine' in field_group.get_attribute('class')
    assert 'dj-touched' not in field_group.get_attribute('class')
    assert 'dj-dirty' not in field_group.get_attribute('class')
    placeholder = page.query_selector('django-formset ul.dj-errorlist > li.dj-placeholder')
    assert placeholder.inner_text() == ''
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    select_left_element.focus()
    assert 'dj-touched' in field_group.get_attribute('class')
    assert 'dj-pristine' in field_group.get_attribute('class')
    assert 'dj-untouched' not in field_group.get_attribute('class')
    assert 'dj-dirty' not in field_group.get_attribute('class')
    page.wait_for_selector('django-formset').evaluate('elem => elem.reset()')
    assert 'dj-untouched' in field_group.get_attribute('class')
    assert 'dj-pristine' in field_group.get_attribute('class')
    assert 'dj-touched' not in field_group.get_attribute('class')
    assert 'dj-dirty' not in field_group.get_attribute('class')
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    select_right_element.focus()
    assert 'dj-touched' in field_group.get_attribute('class')
    assert 'dj-pristine' in field_group.get_attribute('class')
    assert 'dj-untouched' not in field_group.get_attribute('class')
    assert 'dj-dirty' not in field_group.get_attribute('class')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_left_selector_lookup(page, mocker, view, form, viewname):
    sleep(0.25)
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    input_element = page.query_selector('django-formset .dj-dual-selector .left-column input')
    assert input_element is not None
    input_element.focus()
    spy = mocker.spy(view.view_class, 'get')
    page.keyboard.press('6')
    assert spy.called is False
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option') if not o.is_hidden()]
    filtered = [str(o.id) for o, _ in zip(OpinionModel.objects.iterator(), range(DualSelector.max_prefetch_choices)) if '6' in o.label]
    assert set(filtered) == set(left_option_values)
    spy.reset_mock()
    page.keyboard.press('5')
    sleep(0.1)
    page.keyboard.press('3')
    sleep(0.1)
    assert spy.called is True
    option = select_left_element.query_selector('option:not([hidden])')
    assert option.text_content() == "Opinion 0653"
    assert option.get_attribute('value') == str(OpinionModel.objects.get(label__contains='653').pk)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector3'])
def test_right_selector_lookup(page, form, viewname):
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    input_element = page.query_selector('django-formset .dj-dual-selector .right-column input')
    assert input_element is not None
    right_option_values = [o.get_attribute('value') for o in select_right_element.query_selector_all('option') if not o.is_hidden()]
    assert set(right_option_values) == set(str(o) for o in get_initial_opinions())
    input_element.focus()
    page.keyboard.press('4')
    page.keyboard.press('5')
    option = select_right_element.query_selector('option:not([hidden])')
    assert option.text_content() == "Opinion 0045"
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-all-left')
    assert button is not None
    button.click()
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option')]
    assert option.get_attribute('value') in left_option_values
    right_option_values = [o.get_attribute('value') for o in select_right_element.query_selector_all('option')]
    assert option.get_attribute('value') not in right_option_values


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0', 'selector3'])
def test_undo_redo(page, view, form, viewname):
    selector_element = page.query_selector('django-formset select[is="django-dual-selector"]')
    assert selector_element is not None
    initial_values = selector_element.evaluate('elem => elem.value')
    undo_button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-undo-selected')
    assert undo_button is not None
    assert undo_button.is_disabled()
    redo_button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-redo-selected')
    assert redo_button is not None
    assert redo_button.is_disabled()
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    left_option_values = [o.get_attribute('value') for o in select_left_element.query_selector_all('option')]
    select_left_element.focus()
    select_left_element.select_option(left_option_values[68:83])
    move_button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-selected-right')
    assert move_button is not None
    move_button.click()
    assert not undo_button.is_disabled()
    assert redo_button.is_disabled()
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column select')
    assert select_right_element is not None
    select_right_element.query_selector('option[value="{}"]'.format(left_option_values[70])).dblclick()
    assert len(select_right_element.query_selector_all('option')) == 14 + len(initial_values)
    undo_button.click()
    assert not undo_button.is_disabled()
    assert not redo_button.is_disabled()
    right_option_values = [o.get_attribute('value') for o in select_right_element.query_selector_all('option')]
    assert left_option_values[70] in right_option_values
    undo_button.click()
    assert undo_button.is_disabled()
    assert not redo_button.is_disabled()
    right_option_values = [o.get_attribute('value') for o in select_right_element.query_selector_all('option')]
    assert left_option_values[70] not in right_option_values
    assert set(right_option_values) == set(initial_values)
    redo_button.click()
    assert not undo_button.is_disabled()
    assert not redo_button.is_disabled()
    right_option_values = [o.get_attribute('value') for o in select_right_element.query_selector_all('option')]
    assert left_option_values[70] in right_option_values
    redo_button.click()
    assert not undo_button.is_disabled()
    assert redo_button.is_disabled()
    right_option_values = [o.get_attribute('value') for o in select_right_element.query_selector_all('option')]
    assert left_option_values[70] not in right_option_values


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectorP'])
def test_selector_sorting(page, mocker, view, form, viewname):
    select_left_element = page.query_selector('django-formset .dj-dual-selector .left-column select')
    assert select_left_element is not None
    option = select_left_element.query_selector('option:nth-child(40)')
    option.click()
    option = select_left_element.query_selector('option:nth-child(47)')
    option.click(modifiers=['Shift'])
    select_right_element = page.query_selector('django-formset .dj-dual-selector .right-column django-sortable-select')
    assert select_right_element is not None
    assert len(select_right_element.query_selector_all('option')) == 0
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-move-selected-right')
    assert button is not None
    button.click()
    assert len(select_right_element.query_selector_all('option')) == 8
    page.query_selector('django-formset .dj-dual-selector .right-column django-sortable-select option').click()
    page.locator('django-formset .right-column django-sortable-select option:nth-child(7)').click()
    sleep(0.1)
    drag_handle = page.locator('django-formset .right-column django-sortable-select option:nth-child(7)')
    drag_handle.drag_to(page.locator('django-formset .right-column django-sortable-select option:first-child'))
    sleep(0.1)
    drag_handle = page.locator('django-formset .right-column django-sortable-select option:nth-child(3)')
    drag_handle.drag_to(page.locator('django-formset .right-column django-sortable-select option:last-child'))
    sleep(0.1)
    drag_handle = page.locator('django-formset .right-column django-sortable-select option:nth-child(4)')
    drag_handle.drag_to(page.locator('django-formset .right-column django-sortable-select option:nth-child(6)'))
    sleep(0.1)
    button = page.query_selector('django-formset .dj-dual-selector .control-column button.dj-undo-selected')
    assert button is not None
    button.click()
    spy = mocker.spy(view.view_class, 'post')
    submit_button = page.query_selector('django-formset button[click]')
    submit_button.click()
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    labels = [f"Opinion {number:04d}" for number in range(40, 48)]
    expected = [str(o.pk) for o in OpinionModel.objects.filter(label__in=labels)]
    expected.insert(0, expected.pop(6))
    expected.append(expected.pop(2))
    assert request['formset_data']['weighted_opinions'] == expected
    sleep(0.1)
    response = json.loads(spy.spy_return.content)
    assert response == {'success_url': '/success'}
