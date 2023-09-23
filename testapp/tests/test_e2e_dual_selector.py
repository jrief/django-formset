import pytest
import json
from time import sleep

from playwright.sync_api import expect

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
    extra_context = {'click_actions': 'submit -> proceed'}


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
    extra_context={'force_submission': True, 'click_actions': 'submit -> proceed'},
)
views['selectorP'] = ModelFormView.as_view(
    form_class=type('model_poll_form', (ModelPollForm,), {'name': 'selector_required'}),
    extra_context={'force_submission': True, 'click_actions': 'submit -> proceed'},
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
    selector_element = page.locator('django-formset select[is="django-dual-selector"]')
    values = selector_element.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
    if form.name == 'selector_initialized':
        assert set(values) == set(str(k) for k in get_initial_opinions())
    else:
        assert values == []


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', views.keys())
def test_move_all_right(page, mocker, view, form, viewname):
    selector_element = page.locator('django-formset select[is="django-dual-selector"]')
    incomplete = selector_element.get_attribute('incomplete') is not None
    selector_options = selector_element.locator('option')
    if form.name == 'selector_complete':
        assert incomplete is False
        assert selector_options.count() == 100
    else:
        assert incomplete is True
        assert selector_options.count() == DualSelector.max_prefetch_choices
    select_left_element = page.locator('django-formset .dj-dual-selector .left-column select')
    button = page.locator('django-formset .dj-dual-selector .control-column button.dj-move-all-right')
    if viewname == 'selectorP':
        select_right_element = page.locator('django-formset .dj-dual-selector .right-column django-sortable-select')
    else:
        select_right_element = page.locator('django-formset .dj-dual-selector .right-column select')
    select_left_options = select_left_element.locator('option')
    select_right_options = select_right_element.locator('option')
    assert select_left_options.count() + select_right_options.count() == selector_options.count()
    if form.name == 'selector_initialized':
        assert select_right_options.count() == len(get_initial_opinions())
    else:
        assert select_right_options.count() == 0
    spy = mocker.spy(view.view_class, 'get')
    right_option_values = set(select_right_options.nth(i).get_attribute('value') for i in range(select_right_options.count()))
    while incomplete:
        left_option_values = set(select_left_options.nth(i).get_attribute('value') for i in range(select_left_options.count()))
        button.click()  # this triggers loading of more options
        right_option_values = right_option_values.union(left_option_values)
        assert right_option_values == set(select_right_options.nth(i).get_attribute('value') for i in range(select_right_options.count()))
        assert spy.called is True
        assert spy.spy_return.status_code == 200
        content = json.loads(spy.spy_return.content)
        spy.reset_mock()
        assert select_left_options.count() == content['count']
        incomplete = content['incomplete']
        assert content['total_count'] == OpinionModel.objects.filter(tenant=1).count()
        if incomplete:
            assert selector_options.count() < content['total_count']
        else:
            assert selector_options.count() == content['total_count']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0', 'selector3'])
def test_move_selected_right(page, mocker, view, form, viewname):
    select_left = page.locator('django-formset .dj-dual-selector .left-column select')
    left_option_values = set()
    for index in range(30, 39):
        left_option_values.add(select_left.locator(f'option:nth-child({index})').get_attribute('value'))
    select_left.select_option(value=list(left_option_values))
    select_right = page.locator('django-formset .dj-dual-selector .right-column select')
    if form.name == 'selector_initialized':
        expect(select_right.locator('option')).to_have_count(len(get_initial_opinions()))
        left_option_values.update(o.get_attribute('value') for o in select_right.locator('option').all())
    else:
        expect(select_right.locator('option')).to_have_count(0)
    page.locator('django-formset .dj-dual-selector button.dj-move-selected-right').click()
    right_option_values = set(o.get_attribute('value') for o in select_right.locator('option').all())
    assert left_option_values == right_option_values
    option = select_right.locator('option:nth-child(6)')
    option.click()
    option_value = option.get_attribute('value')
    page.locator('django-formset .dj-dual-selector button.dj-move-selected-left').click()
    left_option_values = set(o.get_attribute('value') for o in select_left.locator('option').all())
    right_option_values = set(o.get_attribute('value') for o in select_right.locator('option').all())
    assert option_value in left_option_values
    assert option_value not in right_option_values
    spy = mocker.spy(view.view_class, 'post')
    page.locator('django-formset > p button:first-child').click()
    sleep(0.2)
    spy.assert_called()
    request = json.loads(spy.call_args.args[1].body)
    assert set(request['formset_data']['model_choice']) == right_option_values


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_infinite_scroll(page, mocker, view, form, viewname):
    selector_element = page.locator('django-formset select[is="django-dual-selector"]')
    select_left_element = page.locator('django-formset .dj-dual-selector .left-column select')
    left_options = select_left_element.locator('option')
    left_option_values = [left_options.nth(i).get_attribute('value') for i in range(left_options.count())]
    assert len(left_option_values) == DualSelector.max_prefetch_choices
    select_left_element.focus()
    spy = mocker.spy(view.view_class, 'get')
    select_left_element.select_option(left_option_values[-2])
    assert spy.called is False
    left_option_values = [left_options.nth(i).get_attribute('value') for i in range(left_options.count())]
    assert len(left_option_values) == DualSelector.max_prefetch_choices
    page.keyboard.press('ArrowDown')
    sleep(0.2)
    assert spy.called is True
    field_name = selector_element.get_attribute('name')
    params = spy.call_args.args[1].GET
    assert params['field'] == f'__default__.{field_name}'
    assert int(params['offset']) == DualSelector.max_prefetch_choices
    left_option_values = [left_options.nth(i).get_attribute('value') for i in range(left_options.count())]
    assert len(left_option_values) == 2 * DualSelector.max_prefetch_choices
    response = json.loads(spy.spy_return.content)
    assert response['count'] == DualSelector.max_prefetch_choices
    assert response['incomplete'] is True
    assert isinstance(response['options'], list)
    assert len(response['options']) == response['count']
    spy.reset_mock()
    select_left_element.locator('option[value="{}"]'.format(left_option_values[-1])).click()
    page.keyboard.press('ArrowDown')
    sleep(0.2)
    assert spy.called is True
    left_option_values = [left_options.nth(i).get_attribute('value') for i in range(left_options.count())]
    assert len(left_option_values) == 3 * DualSelector.max_prefetch_choices
    spy.reset_mock()
    select_left_element.locator('option[value="{}"]'.format(left_option_values[-1])).click()
    page.keyboard.press('ArrowDown')
    sleep(0.2)
    assert spy.called is True
    response = json.loads(spy.spy_return.content)
    assert response['incomplete'] is False


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_submit_valid_form(page, mocker, view, form, viewname):
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
    submit_button = page.query_selector('django-formset button[df-click]')
    submit_button.click()
    sleep(0.2)
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
    submit_button = page.query_selector('django-formset button[df-click]')
    submit_button.click()
    assert spy.called is False
    error_ph = page.query_selector('django-formset [role="group"] ul.dj-errorlist > li.dj-placeholder')
    assert error_ph is not None
    assert error_ph.text_content() == form.fields['model_choice'].error_messages['required']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selectorF'])
def test_force_submit_invalid_form(page, mocker, view, form, viewname):
    spy = mocker.spy(view.view_class, 'post')
    submit_button = page.query_selector('django-formset button[df-click]')
    submit_button.click()
    sleep(0.2)
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    assert request['formset_data']['model_choice'] == []
    response = json.loads(spy.spy_return.content)
    assert response['model_choice'] == [form.fields['model_choice'].error_messages['required']]
    error_ph = page.query_selector('django-formset [role="group"] ul.dj-errorlist > li.dj-placeholder')
    assert error_ph is not None
    assert error_ph.text_content() == form.fields['model_choice'].error_messages['required']


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0', 'selector3'])
def test_reset_selector(page, view, form, viewname):
    selector_element = page.locator('django-formset select[is="django-dual-selector"]')
    expect(selector_element).to_be_visible()
    initial_values = selector_element.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
    select_left_element = page.locator('django-formset .dj-dual-selector .left-column select')
    expect(select_left_element).to_be_visible()
    left_option_values = [o.get_attribute('value') for o in select_left_element.locator('option').all()]
    select_left_element.locator('option[value="{}"]'.format(left_option_values[50])).dblclick()
    select_right_element = page.locator('django-formset .dj-dual-selector .right-column select')
    expect(select_right_element).to_be_visible()
    right_option_values = [o.get_attribute('value') for o in select_right_element.locator('option').all()]
    assert set(initial_values).union([left_option_values[50]]) == set(right_option_values)
    values = selector_element.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
    assert values != initial_values
    page.locator('django-formset').evaluate('elem => elem.reset()')
    values = selector_element.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
    assert values == initial_values


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_touch_selector(page, form, viewname):
    field_group = page.locator('django-formset [role="group"]')
    expect(field_group).to_have_class('dj-untouched dj-pristine')
    placeholder = page.locator('django-formset ul.dj-errorlist > li.dj-placeholder')
    expect(placeholder).to_have_text('')
    select_left_element = page.locator('django-formset .dj-dual-selector .left-column select')
    expect(select_left_element).to_be_visible()
    select_left_element.focus()
    expect(field_group).to_have_class('dj-pristine dj-touched')
    page.locator('django-formset').evaluate('elem => elem.reset()')
    expect(field_group).to_have_class('dj-pristine dj-untouched')
    select_right_element = page.locator('django-formset .dj-dual-selector .right-column select')
    expect(select_right_element).to_be_visible()
    select_right_element.focus()
    expect(field_group).to_have_class('dj-pristine dj-touched')


@pytest.mark.urls(__name__)
@pytest.mark.parametrize('viewname', ['selector0'])
def test_left_selector_lookup(page, mocker, view, form, viewname):
    select_left_element = page.locator('django-formset .dj-dual-selector .left-column select')
    expect(select_left_element).to_be_visible()
    input_element = page.locator('django-formset .dj-dual-selector .left-column input')
    expect(input_element).to_be_visible()
    input_element.focus()
    spy = mocker.spy(view.view_class, 'get')
    page.keyboard.press('6')
    assert spy.called is False
    left_option_values = [o.get_attribute('value') for o in select_left_element.locator('option').all() if not o.is_hidden()]
    filtered = [str(o.id) for o, _ in zip(OpinionModel.objects.iterator(), range(DualSelector.max_prefetch_choices)) if '6' in o.label]
    assert set(filtered) == set(left_option_values)
    spy.reset_mock()
    page.keyboard.press('5')
    sleep(0.1)
    page.keyboard.press('3')
    sleep(0.1)
    assert spy.called is True
    option = select_left_element.locator('option:not([hidden])')
    expect(option).to_have_text("Opinion 0653")
    expect(option).to_have_attribute('value', str(OpinionModel.objects.get(label__contains='653').pk))


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
    initial_values = selector_element.evaluate('elem => Array.from(elem.selectedOptions).map(o => o.value)')
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
    select_left_element = page.locator('django-formset .dj-dual-selector .left-column select')
    option = select_left_element.locator('option:nth-child(40)')
    option.click()
    option = select_left_element.locator('option:nth-child(47)')
    option.click(modifiers=['Shift'])
    select_right_element = page.locator('django-formset .dj-dual-selector .right-column django-sortable-select')
    assert select_right_element.locator('option').count() == 0
    page.locator('django-formset .dj-dual-selector .control-column button.dj-move-selected-right').click()
    assert select_right_element.locator('option').count() == 8
    select_right_element.locator('option:first-child').click()
    select_right_element.locator('option:nth-child(7)').click()
    sleep(0.2)  # animation is set to 150ms
    drag_handle = select_right_element.locator('option:nth-child(7)')
    drag_handle.drag_to(select_right_element.locator('option:first-child'))
    sleep(0.2)  # animation is set to 150ms
    drag_handle = select_right_element.locator('option:nth-child(3)')
    drag_handle.drag_to(select_right_element.locator('option:last-child'))
    sleep(0.2)  # animation is set to 150ms
    drag_handle = select_right_element.locator('option:nth-child(4)')
    drag_handle.drag_to(select_right_element.locator('option:nth-child(6)'))
    sleep(0.2)  # animation is set to 150ms
    page.locator('django-formset .dj-dual-selector .control-column button.dj-undo-selected').click()
    spy = mocker.spy(view.view_class, 'post')
    page.locator('django-formset button[df-click]').first.click()
    sleep(0.2)  # animation is set to 150ms
    assert spy.called is True
    request = json.loads(spy.call_args.args[1].body)
    labels = [f"Opinion {number:04d}" for number in range(40, 48)]
    expected = [str(o.pk) for o in OpinionModel.objects.filter(label__in=labels)]
    expected.insert(0, expected.pop(6))
    expected.append(expected.pop(2))
    assert request['formset_data']['weighted_opinions'] == expected
    response = json.loads(spy.spy_return.content)
    assert response == {'success_url': '/success'}
